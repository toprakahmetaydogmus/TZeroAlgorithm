/**
 * T-Zero Model Context Protocol (MCP) Server & AST Context Architect
 * Author: Toprak Ahmet Aydoğmuş (Siber Akademi)
 * Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
 */

export interface TZeroPackageInfo {
  version: string;
  author: string;
  repository: string;
  srcDir: string;
  mcpServer: string;
  cli: string;
}

export declare const version: string;
export declare const author: string;
export declare const repository: string;
export declare const srcDir: string;
export declare const mcpServer: string;
export declare const cli: string;

declare const tzero: TZeroPackageInfo;
export default tzero;

