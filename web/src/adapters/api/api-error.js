export class ApiError extends Error {
  constructor(code, message, status = 400, fieldErrors = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}
