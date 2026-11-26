class Tzero < Formula
  include Language::Python::Virtualenv

  desc "Deterministic AST Context Compressor, 95% Token Reducer & 20-Tool MCP Server"
  homepage "https://github.com/toprakahmetaydogmus/TZeroAlgorithm"
  url "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/archive/refs/tags/v12.3.0.tar.gz"
  sha256 "518b3f09391cea7084bfc7093218effa2f1dcc78ff5b672603d2ca0b322131fa"
  version "12.3.0"
  license "AGPL-3.0-only"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/tzero", "--version"
  end
end

