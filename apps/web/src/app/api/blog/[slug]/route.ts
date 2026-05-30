import { NextRequest } from "next/server";
import { apiClient } from "@/lib/api-client";
import { runBff } from "@/lib/api-auth";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(
  _request: NextRequest,
  { params }: { params: { slug: string } },
) {
  return runBff(() => apiClient.get(`/blog/${params.slug}`));
}
