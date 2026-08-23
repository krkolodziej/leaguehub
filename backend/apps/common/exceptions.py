from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    status_code = response.status_code
    code_by_status = {
        400: "validation_error",
        401: "authentication_required",
        403: "permission_denied",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
    }
    code = code_by_status.get(status_code, "api_error")
    original = response.data
    if status_code == 400 and isinstance(original, dict) and "detail" not in original:
        response.data = {
            "detail": "Request validation failed.",
            "code": code,
            "fields": original,
        }
    else:
        detail = original.get("detail", str(original)) if isinstance(original, dict) else str(original)
        response.data = {"detail": detail, "code": code}
    return response
