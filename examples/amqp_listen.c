// Copyright 2007 - 2021, Alan Antonuk and the rabbitmq-c contributors.
// SPDX-License-Identifier: mit

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <rabbitmq-c/amqp.h>
#include <rabbitmq-c/tcp_socket.h>

#include "utils.h"

int main(int argc, char const *const *argv) {
    char const *hostname;
    int port, status;
    char const *exchange;
    char const *routingkey;
    amqp_socket_t *socket = NULL;
    amqp_connection_state_t conn;

    if (argc < 5) {
        fprintf(stderr, "Usage: amqp_listen host port exchange routingkey\n");
        return 1;
    }

    hostname = argv[1];
    port = atoi(argv[2]);
    exchange = argv[3];
    routingkey = argv[4];

    printf("Connecting to %s:%d...\n", hostname, port);
    conn = amqp_new_connection();

    socket = amqp_tcp_socket_new(conn);
    if (!socket) {
        fprintf(stderr, "Failed to create TCP socket\n");
        return 1;
    }
    printf("TCP socket created successfully\n");

    status = amqp_socket_open(socket, hostname, port);
    if (status) {
        fprintf(stderr, "Socket open failed with error code: %d (%s)\n", status, amqp_error_string2(status));
        return 1;
    }
    printf("Socket opened successfully\n");

    amqp_rpc_reply_t login_reply = amqp_login(conn, "/", 0, 131072, 0, AMQP_SASL_METHOD_PLAIN, "guest", "guest");
    if (login_reply.reply_type != AMQP_RESPONSE_NORMAL) {
        fprintf(stderr, "Login failed: reply_type=%d\n", login_reply.reply_type);
        die_on_amqp_error(login_reply, "Logging in");
    }
    printf("Logged in successfully\n");

    amqp_channel_open(conn, 1);
    amqp_rpc_reply_t channel_reply = amqp_get_rpc_reply(conn);
    if (channel_reply.reply_type != AMQP_RESPONSE_NORMAL) {
        fprintf(stderr, "Channel open failed: reply_type=%d\n", channel_reply.reply_type);
        die_on_amqp_error(channel_reply, "Opening channel");
    }
    printf("Channel opened successfully\n");

    {
        amqp_queue_declare_ok_t *r = amqp_queue_declare(conn, 1, amqp_empty_bytes, 0, 0, 0, 1, amqp_empty_table);
        amqp_rpc_reply_t queue_reply = amqp_get_rpc_reply(conn);
        if (queue_reply.reply_type != AMQP_RESPONSE_NORMAL) {
            fprintf(stderr, "Queue declare failed: reply_type=%d\n", queue_reply.reply_type);
            die_on_amqp_error(queue_reply, "Declaring queue");
        }
        printf("Queue declared successfully\n");

        amqp_bytes_t queuename = amqp_bytes_malloc_dup(r->queue);
        if (queuename.bytes == NULL) {
            fprintf(stderr, "Out of memory while copying queue name\n");
            return 1;
        }

        amqp_queue_bind(conn, 1, queuename, amqp_cstring_bytes(exchange), amqp_cstring_bytes(routingkey), amqp_empty_table);
        amqp_rpc_reply_t bind_reply = amqp_get_rpc_reply(conn);
        if (bind_reply.reply_type != AMQP_RESPONSE_NORMAL) {
            fprintf(stderr, "Queue bind failed: reply_type=%d\n", bind_reply.reply_type);
            die_on_amqp_error(bind_reply, "Binding queue");
        }
        printf("Queue bound successfully\n");

        amqp_basic_consume(conn, 1, queuename, amqp_empty_bytes, 0, 1, 0, amqp_empty_table);
        amqp_rpc_reply_t consume_reply = amqp_get_rpc_reply(conn);
        if (consume_reply.reply_type != AMQP_RESPONSE_NORMAL) {
            fprintf(stderr, "Consume failed: reply_type=%d\n", consume_reply.reply_type);
            die_on_amqp_error(consume_reply, "Consuming");
        }
        printf("Consuming started successfully\n");

        printf("Waiting for messages...\n");
        while (1) {
            amqp_rpc_reply_t res;
            amqp_envelope_t envelope;

            amqp_maybe_release_buffers(conn);

            res = amqp_consume_message(conn, &envelope, NULL, 0);
            if (AMQP_RESPONSE_NORMAL != res.reply_type) {
                if (AMQP_RESPONSE_LIBRARY_EXCEPTION == res.reply_type && AMQP_STATUS_TIMEOUT == res.library_error) {
                    printf("Timeout occurred, continuing to wait...\n");
                    continue;
                }
                fprintf(stderr, "Consume message failed: reply_type=%d, library_error=%d (%s)\n",
                        res.reply_type, res.library_error, amqp_error_string2(res.library_error));
                break;
            }

            printf("Delivery %u, exchange %.*s routingkey %.*s\n",
                   (unsigned)envelope.delivery_tag, (int)envelope.exchange.len, (char *)envelope.exchange.bytes,
                   (int)envelope.routing_key.len, (char *)envelope.routing_key.bytes);

            if (envelope.message.properties._flags & AMQP_BASIC_CONTENT_TYPE_FLAG) {
                printf("Content-type: %.*s\n", (int)envelope.message.properties.content_type.len,
                       (char *)envelope.message.properties.content_type.bytes);
            }
            printf("----\n");

            amqp_dump(envelope.message.body.bytes, envelope.message.body.len);

            amqp_destroy_envelope(&envelope);
        }

        amqp_bytes_free(queuename);
    }

    die_on_amqp_error(amqp_channel_close(conn, 1, AMQP_REPLY_SUCCESS), "Closing channel");
    die_on_amqp_error(amqp_connection_close(conn, AMQP_REPLY_SUCCESS), "Closing connection");
    die_on_error(amqp_destroy_connection(conn), "Ending connection");
    return 0;
}