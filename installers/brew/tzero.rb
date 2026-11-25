class Tzero < Formula
  include Language::Python::Virtualenv

  desc "AST Codebase Context Architect, Token Reducer & Autonomous MCP Engine"
  homepage "https://tzero-indol.vercel.app"
  url "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/archive/refs/tags/v12.2.1.tar.gz"
  sha256 "518b3f09391cea7084bfc7093218effa2f1dcc78ff5b672603d2ca0b322131fa"
  version "12.2.1"
  license "AGPL-3.0-only"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/tzero", "--version"
    system "#{bin}/tzero", "--demo"
    system "#{bin}/tzero", "pc-fixer", "--dry-run"
  end
end

