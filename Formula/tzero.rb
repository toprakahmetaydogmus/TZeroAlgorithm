class Tzero < Formula
  include Language::Python::Virtualenv

  desc "Deterministic AST Context Compressor, 95% Token Reducer & 20-Tool MCP Server"
  homepage "https://github.com/toprakahmetaydogmus/TZeroAlgorithm"
  url "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/archive/refs/tags/v10.9.0.tar.gz"
  version "10.9.0"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/tzero", "--version"
  end
end

