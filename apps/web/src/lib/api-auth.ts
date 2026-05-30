import { NextResponse } from "next/server";

export class UnauthorizedError extends Error {
  constructor(message = "Unauthorized") {
    super(message);
    this.name = "UnauthorizedError";
  }
}

export function optionalAuth(request: Request): string | undefined {
  return request.headers.get("authorization") ?? undefined;
}

export function withAuth(request: Request): string {
  const token = optionalAuth(request);
  if (!token) throw new UnauthorizedError();
  return token;
}

type BffHandler<R> = () => Promise<R>;

export async function runBff<R>(handler: BffHandler<R>): Promise<NextResponse> {
  try {
    const data = await handler();
    return NextResponse.json(data);
  } catch (err) {
    if (err instanceof UnauthorizedError) {
      return NextResponse.json({ detail: err.message }, { status: 401 });
    }
    const message = err instanceof Error ? err.message : "Upstream error";
    const status = /\((\d{3})\)/.exec(message)?.[1];
    return NextResponse.json(
      { detail: message },
      { status: status ? Number(status) : 502 },
    );
  }
}
