export class ApiError extends Error {
  constructor(message: string, public status: number, public code = 'request_failed') {
    super(message);
    this.name = 'ApiError';
  }
}

export async function responseError(response: Response, message: string): Promise<ApiError> {
  let code = 'request_failed';
  try {
    const body: unknown = await response.json();
    if (body && typeof body === 'object' && 'error' in body) {
      const error = body.error;
      if (error && typeof error === 'object' && 'code' in error && typeof error.code === 'string') {
        code = error.code;
      }
    }
  } catch {
    // Proxies can return HTML; preserve the HTTP status and safe resource message.
  }
  return new ApiError(message, response.status, code);
}
