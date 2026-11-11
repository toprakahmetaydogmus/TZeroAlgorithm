# T-Zero Algorithm

[![PyPI](https://img.shields.io/pypi/v/tzero-mcp)](https://pypi.org/project/tzero-mcp/)
[![npm](https://img.shields.io/npm/v/tzero-mcp)](https://www.npmjs.com/package/tzero-mcp)
[![M8ven](https://m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm?variant=verified)](https://m8ven.ai/mcp/toprakahmetaydogmus/tzeroalgorithm)
[![VS Code](https://img.shields.io/visual-studio-marketplace/v/siber-akademi.tzero-vscode)](https://marketplace.visualstudio.com/items?itemName=siber-akademi.tzero-vscode)
[![Glama](https://img.shields.io/badge/registry-Glama-635bff)](https://glama.ai/mcp/servers/toprakahmetaydogmus/TZeroAlgorithm)
[![CI](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml/badge.svg)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab)](pyproject.toml)
[![Lisans](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[English](README.md) · Türkçe · [Gizlilik politikası](PRIVACY.md)

**Dizinler ve demolar**

[![MCP Servers](https://mcpservers.org/badge.svg)](https://mcpservers.org/servers/toprakahmetaydogmus/tzeroalgorithm)
[![AI Agents Listing](https://img.shields.io/badge/AI%20Agents-Listing-6366f1)](https://aiagentslisting.com/mcp/t-zero-algorithm)
[![MCP Observatory](https://img.shields.io/badge/MCP%20Observatory-Listing-0f766e)](https://mcpobservatory.com/servers/github%3Atoprakahmetaydogmus/TZeroAlgorithm)
[![Skillful](https://img.shields.io/badge/Skillful-Directory-2d6a4f)](https://skillful.sh/mcp/tzero-mcp)
[![Hugging Face Space](https://img.shields.io/badge/Hugging%20Face-Space-ffca28?logo=huggingface)](https://huggingface.co/spaces/toprakke4/tzero-token-reducer)
[![Vercel Hub](https://img.shields.io/badge/Vercel-Project%20Hub-000000?logo=vercel)](https://tzero-indol.vercel.app)
[![Smithery durumu](https://img.shields.io/badge/Smithery-eski%20kayit%20erisilemiyor-lightgrey)](https://www.smithery.ai/future)

Smithery'nin eski T-Zero kayıt ve rozet bağlantıları şu anda 404 dönüyor. Dizin Ekim 2026'da değişti ve güncel bir T-Zero kaydı doğrulanamadı. Smithery durum rozeti, sağlayıcının duyurusuna yönlendirir.

T-Zero, kodlama asistanları için yerel kaynak kodundan bağlam oluşturur. Fonksiyon imzalarını, import ifadelerini ve bağımlılıkları çıkarır. CLI ve MCP sunucusu üzerinden kullanılabilir.

## Ne işe yarar?

Bir kodlama asistanının, ilgili modüllerin bütün uygulama ayrıntılarından önce arayüzlerini ve ilişkilerini görmesi gerekebilir. T-Zero bu bağlamı bildirimlere ve ilişkilere indirgemeye yardımcı olur. Ortaya çıkan metne CLI veya MCP araçlarıyla erişebilirsiniz. Hangi dosyayı inceleyeceğinize ve ne zaman tam kaynak isteyeceğinize siz karar verirsiniz.

- **Python AST budama** kodu ayrıştırıp fonksiyon gövdelerini küçültürken yapısal imzaları korur. Desteklenen diğer diller için dile özel küçültücüler ve yapılandırıldığında isteğe bağlı ayrıştırıcı adaptörleri kullanılır.
- **Bağlam seçimi** odak dosyasını tam tutarken ilişkili dosyaları daha küçük iskeletler olarak sunabilir. Anlık görüntü ve bağımlılık araçları ilgili bağlamı bulmaya yardımcı olur.
- **Token bütçesine göre paketleme** bağlamı hedef bütçeye göre sıralar. Önbellek uyumlu mod, sabit bağlamı değişen görev ayrıntılarından önce yerleştirir.
- **Yerel kontroller** arasında olası gizli bilgi taraması, mimari denetimler ve tanı ile kod eylemleri sunan dil sunucusu bulunur. Değişiklikleri uygulamadan önce sonuçları inceleyin.

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

## Token azaltma ve ölçümler

T-Zero, kodun yararlı yapısını koruyup uygulama ayrıntılarının bir bölümünü çıkararak bağlamı küçültür. Python kodu standart kütüphanedeki `ast` modülüyle ayrıştırılır. Çok dilli küçültücü JavaScript, TypeScript, Rust, Go, C/C++, Java, C#, Solidity, Ruby, PHP, Swift, Kotlin, Dart, Scala ve Elixir dillerini de destekler. Sonuç, kullanılan ayrıştırıcıya veya küçültücüye ve kaynak koda bağlıdır. İskelet, görevi tamamlamak için gereken ayrıntıları çıkarmış olabilir. Çıktıyı inceleyin ve gerektiğinde tam kodu alın.

Örneğin varsayılan Python küçültücüsü şu girdiyi:

```python
def greet(name: str) -> str:
    message = "Hello, " + name
    return message
```

şu yapısal özete dönüştürür:

```python
def greet(name: str) -> str: ...
```

Fonksiyon imzası görünür kalır. Uygulama gövdesi çıkarıldığı için çıktı çalıştırılmak üzere değil, bağlam oluşturmak üzere kullanılır.

Depodaki **temel benchmark** üç sentetik Python görevi kullanır. Her karşılaştırmada hedef uygulama tam tutulur. Bağımlılık için ise tam kaynak veya AST iskeleti kullanılır. Aşağıdaki sonuçlar 11 Kasım 2026'da `tiktoken` ve `cl100k_base` kodlamasıyla yerelde yeniden üretildi.

| Görev | Tam bağlam | Küçültülmüş bağlam | Azalma |
| --- | ---: | ---: | ---: |
| TASK-01 | 502 token | 375 token | %25,3 |
| TASK-02 | 322 token | 239 token | %25,8 |
| TASK-03 | 332 token | 283 token | %14,8 |
| **Toplam** | **1.156 token** | **897 token** | **%22,4** |

Benchmark, üç görev yüzdesinin aritmetik ortalamasını **%21,9** olarak bildirir. Toplam satırı `(1.156 − 897) / 1.156` hesabını kullandığı için ağırlıklı azalma %22,4'tür. Bu örnekler tüm depolar için bir tasarruf oranı veya model doğruluğu göstermez. Farklı kod tabanlarında ve tokenizer'larda sonuçlar değişir.

Örneği kaynak kodu kopyasının kök klasöründe yeniden çalıştırabilirsiniz. `tiktoken` isteğe bağlıdır ve PyPI üzerinden edinilebilir. Paket veya kodlama kullanılamıyorsa benchmark kesin BPE sayısı yerine karakter temelli tahmine geçer. Önbellekte olmayan bir kodlamanın ilk yüklemesi indirme gerektirebilir.

```sh
python -m pip install tiktoken
python tzero_task_benchmark.py
```

Benchmark'ın geçiş kontrolleri, sözdizimini ve çağrılan metot adlarını küçültülmüş örnekle karşılaştırır. Bunlar uygulamanızın testlerinin yerini tutmaz. Kendi projenizde `tzero --scan . --format json` ile ham ve azaltılmış sayıları inceleyebilirsiniz. JSON taraması ham token sayısını dosya baytlarını dörde bölerek, küçültülmüş token sayısını ise karakter sayısını dörde bölerek tahmin eder. Bunlar tablodaki BPE ölçümleri değildir.

Hedef token bütçesiyle bir bağlam paketi oluşturmak için proje klasöründe şu komutu kullanın:

```sh
tzero --pack 16000 --focus path/to/file.py --cache-aligned --pack-out context.txt
```

`context.txt` kaynak kodu ve başka proje bilgileri içerebilir. Bir asistana vermeden önce dosyayı inceleyin.

### Mevcut bağlamın kayıpsız güncellenmesi

Her iki tarafta da aynı önceki bağlam dosyası varsa değişen baytları delta olarak aktarabilirsiniz. T-Zero ortak başlangıç ve bitiş bölümlerini bulur, değişen orta bölümü delta dosyasına yazar. SHA-256 kontrolleri hem temel dosyayı hem geri yüklenen baytları doğrular.

```sh
tzero --context-delta previous.txt current.txt update.tzd
tzero --restore-context previous.txt update.tzd restored.txt
```

Her iki komut için yeni çıktı yolları kullanın. Alıcının birebir aynı temel dosyaya ihtiyacı vardır. Örneğin yerel CLI kaynağına 24 baytlık bir yorum eklediğimde **480.538 baytlık** güncel dosya için **108 baytlık** delta oluştu. Bu, **aktarılan baytta %99,98 azalma** demektir. Ortak içeriği az olan dosyalarda delta, kaynak dosyadan daha büyük olabilir. Delta bir ikili aktarım biçimidir. Model bağlamına vermeden önce geri yükleyin. Modelin token sayısı, modele verilen metne bağlıdır.

Proje notları [yol haritasında](main/ROADMAP.md) ve [uygulama rehberinde](main/WALKTHROUGH.md) bulunur.

## Özellikler

- Kod yapısını ve bağımlılıklarını çıkarma.
- Yerel kod arama ve değişiklik etkisi analizi.
- Olası gizli bilgi ve mimari kural ihlallerini tarama.
- AST anlık görüntüleri ve sabit önekli bağlam paketleri.
- API sözleşme değişiklikleri ve SARIF raporları.
- Hover bilgisi ve kod eylemleri sunan stdio dil sunucusu.
- SCIP indeksleri ve depolar arası manifest paylaşımı.

Varsayılan MCP kataloğu, `search_tools` dahil 21 araç sunar. Başlangıçta 58 aracın tamamını açmak için `TZERO_MCP_TOOL_MODE=all` ayarlanabilir. Araç açıklamalarından dosyaları okuyup okumadığını veya değiştirdiğini kontrol edin.

### CLI ve entegrasyonlar

| Komut | Amaç |
| --- | --- |
| `tzero --scan . --format json` | Çalışma alanını ve bağlam ölçümlerini incelemek. |
| `tzero --pipe example.py` | Standart girdiden kaynak kodu okumak ve dosya adı ipucuyla küçültmek. |
| `tzero --snapshot .` | Artımlı çalışma için AST anlık görüntüsü oluşturmak. |
| `tzero --lsp` | Editör entegrasyonları için stdio dil sunucusunu başlatmak. |
| `tzero --hook-install all` | Desteklenen yapay zekâ istemcileri için yaşam döngüsü kancalarını kurmak. Yapılandırma dosyaları yazar. |
| `tzero --contracts HEAD~1 --contracts-sarif report.sarif` | API sözleşmelerini Git referansıyla karşılaştırıp SARIF raporu yazmak. |
| `tzero --federation impact --federation-symbol SYMBOL` | Bir sembolün depolar arası etkisini incelemek. |
| `tzero --doctor --deep` | Çevrimdışı alt sistem denetimlerini çalıştırmak. |

VS Code/Cursor eklentisi dil sunucusu, kanca ve federasyon komutlarını ekler. Dashboard yerel bir tarayıcı arayüzü sunar. Ayrı PC-Fixer sunucusunda dosyaları veya sistem durumunu değiştirebilen tanı ve onarım araçları da bulunur.

Kaynak sürümü 10.9.0'dır. Paket kayıtları, yayımlama tamamlanana kadar daha eski bir sürüm sunabilir.

## Sınırlar ve gizlilik

Bağlam küçülmesi dile, projeye ve seçilen moda göre değişir. Python için standart AST ayrıştırıcısı kullanılır. Diğer dillerde yapısal sezgisel yöntemler kullanılabilir. Çıktıyı değişiklik yapmadan önce inceleyin.

Gizli bilgi taraması bazı anahtarları kaçırabilir veya zararsız metni işaretleyebilir. Onarım uygulamadan önce bulguları kontrol edin. Bazı araçlar dosyaları veya sistem durumunu değiştirir.

Yerel analiz için bulut modeli gerekmez. Bağlanan MCP istemcisi, araçların döndürdüğü kaynak parçalarını kendi model sağlayıcısına gönderebilir. İsteğe bağlı ağ özellikleri, bağımlılık kurulumu ve ilk tokenizer indirmesi dış hizmetlere bağlanabilir. Ayrıntılar [gizlilik politikasında](PRIVACY.md) bulunur.

## Geri bildirim

[Issue açarken](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/issues) işletim sistemi, sürüm, komut, beklenen sonuç ve küçük bir örnek ekleyin. Kimlik bilgilerini, kişisel dosya yollarını ve özel kaynak kodunu paylaşmadan önce kaldırın.

Geliştirici Toprak Ahmet Aydoğmuş. [MIT lisansı](LICENSE).
