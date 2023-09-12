from enum import Enum


class ErrorCode(Enum):
    # 1xx series, informational response

    # 2xx series, successful
    #   200, request succeed but business error
    no_information_update = 20001
    file_exist = 20002

    # 3xx series, redirection

    # 4xx series, client error
    #   400, bad request
    file_invalid = 40001
    #   401, unauthorized
    no_user_found = 40101

    # 5xx series, server error
    database_operation_error = 50001
    IO_operation_error = 50002


class HTTPStatusCode(Enum):
    ok = 200

    bad_request = 400
    unauthorized = 401
    payment_required = 402
    forbidden = 403
    not_found = 404
    request_timeout = 408

    internal_server_error = 500
    bad_gateway = 502
    service_unavailable = 503
    gateway_timeout = 504
