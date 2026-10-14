# Análise inicial — 14/10/2026

## Entradas examinadas localmente

- Programs64.rar: 335 arquivos extraídos, 504.895.334 bytes, sem erros reportados pelo libarchive.
- CorelDRW.exe: PE32+ x86-64, 395.368 bytes. Recursos de versão indicam 25.1.0.269 / CorelDRAW 2024.
- SHA-256 do executável: `8a5d3952cb1581366417f6e26d268db7ed933ddfa885190f8fc5b71444c9e1ab`.
- Referência visual: captura de interface e quadros de uma gravação de aproximadamente 79 segundos. A barra de título indica CorelDRAW 2026; essa referência não comprova equivalência com os binários 2024.
- Documento CDR fornecido: estrutura ZIP íntegra no teste CRC; contém dados de página, bitmaps, estilos, paleta, metadados e prévias PNG. O conteúdo vetorial proprietário não foi decodificado.

Os arquivos fornecidos, desenhos, imagens e binários proprietários não são distribuídos neste repositório público.

## REA efetivamente executado

REA 6.4.0 foi obtido por npm e executado via CLI. `doctor --client codex --json` identificou Node compatível, ausência de registro MCP e ausência dos motores Ghidra, Hopper e IDA. CLI permite inspeções independentes de registro MCP.

`rea inspect-pe-resources /caminho/CorelDRW.exe --format json` concluiu a inspeção de recursos PE sem executar o alvo. Identificador da evidência:

`ev_da3d9f3ff61fc8e45574567343b6a68a1351dfaa161ad7031b2479624b5e4b1d`

**Nenhuma função nativa foi decompilada.** Falta um motor compatível para essa etapa. A inspeção de recursos não demonstra semântica das ferramentas de desenho. Não foram alteradas configurações globais de clientes nem instalados motores de análise.

## Observações por ferramentas comuns

`objdump -p` mostrou importações de CrlConfig e funções LoadAppDll/RunAppDll no caminho de inicialização. VGCore importa módulos como CdrCore, NodeEditToolCore, BezierFreeHandToolCore, FillToolCore, TextToolCore e outros. Nomes de módulos sugerem responsabilidades, mas não provam os algoritmos internos.

## Implementação

O editor Python/Tk é uma implementação independente. O modelo de documento usa primitivas geométricas, curvas cúbicas e persistência JSON. Não é uma tradução de funções proprietárias e não depende das DLLs fornecidas. O comando de prévia CDR lê exclusivamente um PNG embutido em ZIP.

## Validação e pendências

Testes de modelo executados localmente. Compilação sintática Python executada. Este ambiente não possui display gráfico; a instalação de Xvfb falhou por limitações de permissões do ambiente. A execução interativa em Windows ainda precisa ser confirmada; o workflow inclui teste de interface e geração do executável.

Próximas etapas: disponibilizar motor nativo para REA; validar fluxo visual em Windows; expandir ferramentas; pesquisar e implementar suporte CDR real com testes de equivalência. Não se alega reconstrução integral.
