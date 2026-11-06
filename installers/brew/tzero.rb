class Tzero < Formula
  include Language::Python::Virtualenv

  desc "AST Codebase Context Architect, Token Reducer & Autonomous MCP Engine"
  homepage "https://tzero-indol.vercel.app"
  url "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/archive/refs/tags/v10.6.0.tar.gz"
  sha256 "dcc04131709154120ddf52c986e955f2692ae874e16c2276d718323eada6ff38"
  version "10.6.0"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/tzero", "--version"
    system "#{bin}/tzero", "pc-fixer", "--dry-run"
  end
end

