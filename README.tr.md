# T-Zero Algorithm

[English](README.md) · Türkçe · [Gizlilik politikası](PRIVACY.md)

[![PyPI](https://img.shields.io/pypi/v/tzero-mcp)](https://pypi.org/project/tzero-mcp/)
[![npm](https://img.shields.io/npm/v/tzero-mcp)](https://www.npmjs.com/package/tzero-mcp)
[![M8ven](https://m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm?variant=verified)](https://m8ven.ai/mcp/toprakahmetaydogmus/tzeroalgorithm)
[![Lisans](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

T-Zero, kodlama asistanları için yerel kaynak kodundan bağlam oluşturur. Fonksiyon imzalarını, import ifadelerini ve bağımlılıkları çıkarır. CLI ve MCP sunucusu üzerinden kullanılabilir.

## Kurulum

Python 3.11 veya üzeri gerekir.

```sh
python -m pip install --upgrade tzero-mcp
```

Node.js kuruluysa MCP sunucusunu aşağıdaki komutla başlatabilirsiniz.

```sh
npx -y tzero-mcp@latest
```

Windows dosyaları [sürümler sayfasında](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases) bulunur. Uygulama için `TZeroAlgorithm.exe`, MCP sunucusu için `TZeroMCP.exe`, istemci yapılandırması için `AddMCP.exe` kullanılır. Çalıştırmadan önce dosyanın SHA-256 değerini yayımlanan sağlama toplamıyla karşılaştırın.

## İlk kullanım

İncelemek istediğiniz proje klasöründe çalıştırın.

```sh
tzero --scan . --format json
tzero --doctor --deep
```

`--doctor --deep` yerel alt sistemleri denetler. Desteklenen editörleri yapılandırmak için `tzero init`, tüm seçenekler için `tzero --help` kullanın. Elle MCP kurulumu için [İngilizce kılavuzdaki örneğe](README.md#first-use) bakın.

## Özellikler

- Kod yapısını ve bağımlılıklarını çıkarma.
- Yerel kod arama ve değişiklik etkisi analizi.
- Olası gizli bilgi ve mimari kural ihlallerini tarama.
- AST anlık görüntüleri ve sabit önekli bağlam paketleri.
- API sözleşme değişiklikleri ve SARIF raporları.
- Hover bilgisi ve kod eylemleri sunan stdio dil sunucusu.
- SCIP indeksleri ve depolar arası manifest paylaşımı.

Varsayılan MCP kataloğu, `search_tools` dahil 21 araç sunar. Başlangıçta 58 aracın tamamını açmak için `TZERO_MCP_TOOL_MODE=all` ayarlanabilir. Araç açıklamalarından dosyaları okuyup okumadığını veya değiştirdiğini kontrol edin.

Kaynak sürümü 10.9.0'dır. Paket kayıtları, yayımlama tamamlanana kadar daha eski bir sürüm sunabilir.

## Sınırlar ve gizlilik

Bağlam küçülmesi dile, projeye ve seçilen moda göre değişir. Python için standart AST ayrıştırıcısı kullanılır. Diğer dillerde yapısal sezgisel yöntemler kullanılabilir. Çıktıyı değişiklik yapmadan önce inceleyin.

Gizli bilgi taraması bazı anahtarları kaçırabilir veya zararsız metni işaretleyebilir. Onarım uygulamadan önce bulguları kontrol edin. Bazı araçlar dosyaları veya sistem durumunu değiştirir.

Yerel analiz için bulut modeli gerekmez. Bağlanan MCP istemcisi, araçların döndürdüğü kaynak parçalarını kendi model sağlayıcısına gönderebilir. İsteğe bağlı ağ özellikleri, bağımlılık kurulumu ve ilk tokenizer indirmesi dış hizmetlere bağlanabilir. Ayrıntılar [gizlilik politikasında](PRIVACY.md) bulunur.

## Geri bildirim

[Issue açarken](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/issues) işletim sistemi, sürüm, komut, beklenen sonuç ve küçük bir örnek ekleyin. Kimlik bilgilerini, kişisel dosya yollarını ve özel kaynak kodunu paylaşmadan önce kaldırın.

Geliştirici Toprak Ahmet Aydoğmuş. [MIT lisansı](LICENSE).
