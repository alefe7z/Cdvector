# cdvector

Editor vetorial desktop independente, com interface escura em português e destino Windows.
**Versão 0.1: protótipo funcional inicial. Não é equivalente completo ao CorelDRAW e não contém código decompilado dele.**

## Baixar para Windows

Abra a aba **Actions → Build Windows**, selecione uma execução concluída com sucesso e baixe o artefato **cdvector-windows**. Extraia e abra `cdvector.exe`. É necessário estar conectado ao GitHub para baixar artefatos. O executável não possui assinatura digital.

Se a execução falhar ou ainda não houver artefato, use uma das opções locais abaixo. Não se presume que a compilação passou apenas porque o workflow foi enviado.

## Executar pelo código

Instale Python 3.12 para Windows com Tcl/Tk (incluído no instalador padrão). Baixe o código e abra `run-windows.bat`, ou execute na pasta do projeto:

```console
py -3 -m cdvector
```

A aplicação utiliza apenas a biblioteca padrão do Python. Para produzir um executável local, execute `build-windows.bat`: ele cria um ambiente virtual e instala PyInstaller 6.16.0. Saída: `dist/cdvector.exe`.

## Recursos implementados

- Retângulos, elipses, linhas, texto e curvas Bézier cúbicas.
- Seleção, movimentação, duplicação, exclusão e ordem de sobreposição.
- Edição dos pontos de controle com a ferramenta **Editar pontos**.
- Preenchimento, contorno, espessura e tamanho de texto.
- Desfazer/refazer com até 100 estados, zoom e deslocamento da vista.
- Salvar/abrir projetos `.cdvector` em JSON e exportar SVG vetorial.
- Prévia de arquivos CDR que contenham PNG embutido (não importa objetos editáveis).

## Uso

Escolha uma forma e arraste na página. Para Bézier, clique quatro vezes: início, primeiro controle, segundo controle e fim. Em **Editar pontos**, arraste os marcadores. As curvas são abertas; o preenchimento delas não está implementado.

Clique numa cor para definir o preenchimento; botão direito define o contorno. Use a roda do mouse para zoom e o botão do meio para mover a vista.

Atalhos: V selecionar; N pontos; R retângulo; E elipse; L linha; B Bézier; T texto. Ctrl+S salva; Ctrl+O abre; Ctrl+N cria; Ctrl+Z desfaz; Ctrl+Y refaz; Ctrl+D duplica; Delete exclui; Esc cancela desenho em andamento.

A página inicial é A3 vertical. Coordenadas e espessuras usam pixels SVG (96 px/polegada). Réguas em pixels. Não há gestão CMYK/ICC nesta versão.

## Limitações conhecidas

Sem leitura/escrita completa de CDR, importação SVG, importação de imagens, grupos, múltiplas páginas, operações booleanas, rotação, alinhamento, gradientes, impressão ou efeitos avançados. As curvas na tela usam amostragem; a exportação mantém a Bézier matemática. Métricas de texto podem variar entre Tk e visualizadores SVG. Seleção de formas vazias é pelo contorno.

## Verificação

```console
python -m unittest discover -s tests -v
```

Os testes de modelo verificam persistência, SVG, curvas, histórico e rejeição de dados inválidos. O teste de interface executa no Windows CI; em ambientes Linux sem display, é explicitamente ignorado.

Veja [a análise inicial e os limites de evidência](docs/analysis.md).
