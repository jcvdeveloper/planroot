/**
 * Planroot Cloudflare Worker
 * Roteia /api/* para o backend (FastAPI/Render/Railway)
 * Os assets estáticos são servidos automaticamente pelo Cloudflare Pages
 */

export default {
  async fetch(request: Request, env: any, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // Rotear /api/* para o backend
    if (url.pathname.startsWith('/api/')) {
      return handleApiRequest(request);
    }

    // Para outras rotas, deixar Cloudflare Pages servir (index.html ou assets)
    return new Response('Not Found', { status: 404 });
  },
};

/**
 * Rotear requisições /api/* para o backend
 * TODO: Altere para sua URL de backend em produção
 */
async function handleApiRequest(request: Request): Promise<Response> {
  const url = new URL(request.url);

  // ⚠️ IMPORTANTE: Configure a URL do seu backend aqui
  // Exemplos:
  // - http://localhost:8000 (desenvolvimento)
  // - https://planroot-api.render.com (produção com Render)
  // - https://planroot-api.railway.app (produção com Railway)

  const backendUrl = `http://localhost:8000${url.pathname}${url.search}`;

  try {
    const response = await fetch(backendUrl, {
      method: request.method,
      headers: new Headers(request.headers),
      body: request.body,
    });

    return response;
  } catch (error) {
    console.error('Backend error:', error);
    return new Response(
      JSON.stringify({
        error: 'Backend não disponível',
        message: (error as Error).message,
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
