export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">MCP Forge</h1>
        <p className="text-lg text-[var(--text-muted)]">
          Turn any OpenAPI or Swagger specification into a robust, ready-to-run Model Context Protocol (MCP) server.
        </p>
      </div>
    </main>
  );
}
