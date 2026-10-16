import { Container, getContainer } from "@cloudflare/containers";

interface Env {
  ETEWITTER_CONTAINER: DurableObjectNamespace<EtewitterContainer>;
  DJANGO_SECRET_KEY: string;
  DJANGO_ALLOWED_HOSTS: string;
}

export class EtewitterContainer extends Container {
  defaultPort = 8080;
  sleepAfter = "10m";
  pingEndpoint = "login/";

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    this.envVars = {
      DJANGO_DEBUG: "False",
      DJANGO_SECRET_KEY: env.DJANGO_SECRET_KEY,
      DJANGO_ALLOWED_HOSTS: `container,${env.DJANGO_ALLOWED_HOSTS}`,
      TRUST_PROXY_HEADERS: "True",
    };
  }
}

export default {
  fetch(request: Request, env: Env): Promise<Response> {
    const headers = new Headers(request.headers);
    headers.set("x-forwarded-proto", new URL(request.url).protocol.slice(0, -1));
    const forwarded = new Request(request, { headers });
    return getContainer(env.ETEWITTER_CONTAINER, "etewitter").fetch(forwarded);
  },
} satisfies ExportedHandler<Env>;
