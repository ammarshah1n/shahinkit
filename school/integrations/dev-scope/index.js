import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { createScope, PublicError, toToolResult } from './lib/scope.js';

const configPath = process.env.DEV_SCOPE_CONFIG ?? new URL('./config.json', import.meta.url);

function run(handler) {
  return async (input) => {
    try {
      return toToolResult(await handler(input));
    } catch (error) {
      return toToolResult(error instanceof PublicError ? error : new PublicError('REQUEST_FAILED'));
    }
  };
}

let scope;
try {
  scope = await createScope(configPath);
} catch {
  process.stderr.write('dev-scope: configuration unavailable\n');
  process.exit(1);
}

const server = new McpServer({ name: 'dev-scope', version: '1.0.0' });
const rootId = z.string().min(1).max(64);
const relativePath = z.string().min(1).max(512);

server.registerTool(
  'list_projects',
  { description: 'List configured read-only project IDs.', inputSchema: {} },
  run(async () => scope.listProjects())
);

server.registerTool(
  'project_overview',
  { description: 'List approved locations and read-only git metadata for one project.', inputSchema: { rootId } },
  run(async ({ rootId: id }) => scope.overview(id))
);

server.registerTool(
  'read_file',
  { description: 'Read one approved text file by root ID and relative path.', inputSchema: { rootId, path: relativePath } },
  run(async ({ rootId: id, path }) => scope.readFile(id, path))
);

server.registerTool(
  'list_directory',
  { description: 'List one approved directory by root ID and relative path.', inputSchema: { rootId, path: relativePath } },
  run(async ({ rootId: id, path }) => scope.listDirectory(id, path))
);

server.registerTool(
  'search_code',
  {
    description: 'Perform bounded literal search in approved text files.',
    inputSchema: { rootId: rootId.optional(), query: z.string().min(1).max(256) }
  },
  run(async ({ rootId: id, query }) => scope.search(id, query))
);

server.registerTool(
  'git_status',
  { description: 'Read git status and recent commits for one configured project.', inputSchema: { rootId } },
  run(async ({ rootId: id }) => scope.gitStatus(id))
);

await server.connect(new StdioServerTransport());
