from bs4 import BeautifulSoup

from src.scraper.infrastructure.external.html_utils import remove_elements


def test_remove_elements_with_complex_css_selector():
    """
    Verifica se a função remove_elements consegue lidar com seletores CSS complexos.
    Este teste falhará com a implementação atual, reproduzindo o bug #10.
    """
    # Arrange: HTML de exemplo e um seletor CSS complexo
    html = """
    <html>
        <body>
            <div>
                <h1>Título para Remover</h1>
                <p>Este parágrafo deve permanecer.</p>
            </div>
            <h1>Este título não deve ser removido</h1>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    selectors_to_remove = ["div > h1"]

    # Act: Executa a função de remoção
    remove_elements(soup, selectors_to_remove)

    # Assert: Verifica se o elemento h1 aninhado foi removido
    # e se o h1 não aninhado permaneceu
    assert soup.select_one("div > h1") is None
    assert soup.select_one("h1").text == "Este título não deve ser removido"
    assert soup.select_one("p").text == "Este parágrafo deve permanecer."

def test_remove_elements_with_tag_selector():
    """Verifica a remoção por nome de tag."""
    html = "<body><h1>Title</h1><p>Text</p></body>"
    soup = BeautifulSoup(html, "html.parser")
    remove_elements(soup, ["h1"])
    assert soup.find("h1") is None
    assert soup.find("p") is not None

def test_remove_elements_with_class_selector():
    """Verifica a remoção por seletor de classe."""
    html = '<body><p class="remove-me">Remove</p><p>Keep</p></body>'
    soup = BeautifulSoup(html, "html.parser")
    remove_elements(soup, [".remove-me"])
    assert soup.select_one(".remove-me") is None
    assert soup.find("p").text == "Keep"
