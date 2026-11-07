class Tzero < Formula
  include Language::Python::Virtualenv

  desc "Deterministic AST Context Compressor, 95% Token Reducer & 20-Tool MCP Server"
  homepage "https://github.com/toprakahmetaydogmus/TZeroAlgorithm"
  url "https://github.com/toprakahmetaydogmus/TZeroAlgorithm/archive/refs/tags/v10.7.4.tar.gz"
  sha256 "3352577ad456b5c9764889e7c768117a6db01a707a866d5dcd40b5e72b3ff1aa"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/tzero", "--version"
  end
end
