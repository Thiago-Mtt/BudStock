from flask import Flask, render_template, url_for, flash, redirect, request
import sqlite3

conn = sqlite3.connect('teste.db', check_same_thread=False)
conn.execute("PRAGMA foreign_keys = 1")
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS Estoques(
    codEstoque INTEGER PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL
)""")

conn.commit()


class Estoque:
    # 1 ATRIBUTO ; 1 METODOS

    def __init__(self, estoque):
        # estoque = nome do estoque;
        self.estoque = estoque

    def criar_tabela(self):
        # Insere o estoque no banco de dados e cria uma tabela correspondente
        # Não é possível inserir o estoque se o nome já estiver ocupado
        c.execute("SELECT * FROM Estoques WHERE nome=?", (self.estoque,))
        check = c.fetchone()
        if not check:
            with conn:
                c.execute("INSERT INTO Estoques (nome) VALUES (?)", (self.estoque,))
            with conn:
                c.execute("""CREATE TABLE IF NOT EXISTS [""" + self.estoque + """](
            numero INTEGER NOT NULL,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preço REAL NOT NULL,
            estoque INTEGER NOT NULL,
            FOREIGN KEY (estoque) REFERENCES Estoques(codEstoque) ON DELETE CASCADE
            )""")

    @staticmethod
    def remover_estoque(nome_estoque):
        # Recebe o nome do estoque
        # Remove o estoque do Banco e os produtos contidos nesse estoque
        with conn:
            c.execute("DELETE FROM Estoques WHERE nome=?", (nome_estoque,))

    def mostrar_estoque(self):
        # Para testes: printa o estoque
        with conn:
            c.execute("SELECT numero,nome,preço,quantidade FROM [" +self.estoque+ "] ORDER BY numero")
        return (c.fetchall())

    @staticmethod
    def mostrar_estoques():
        # Para testes: printa os estoques no banco
        c.execute("SELECT * FROM Estoques")
        return c.fetchall()


class Produto:
    # 5 ATRIBUTOS; 3 METODOS

    def __init__(self, numero, nome, quantidade, preço, estoque_nome):

        # O ultimo atributo recebe o nome do estoque ao qual o produto pertence
        self.numero = numero
        self.nome = nome
        self.quantidade = quantidade
        self.preço = preço
        self.estoque_nome = estoque_nome

    def produto_novo(self):

        # Insere o produto na tabela correspondente ao seu estoque
        # Caso o Numero OU o Nome já estejam ocupados, o metodo não insere o produto
        c.execute("SELECT * FROM " + self.estoque_nome + " WHERE nome=? OR numero=? ", (self.nome, self.numero))
        check = c.fetchone()
        if not check:
            if self.numero and self.nome and self.preço and self.quantidade:
                c.execute("SELECT * FROM Estoques WHERE nome = ?", (self.estoque_nome,))
                lista = c.fetchone()
                c.execute("INSERT INTO [" + self.estoque_nome + "] VALUES (?, ?, ?, ?, ?)", (self.numero, self.nome,
                                                                                           self.preço, self.quantidade,
                                                                                           lista[0]))
                conn.commit()

    def alterar_produto(self, nro_prod):

        # Atualiza todas as informações do produto com o Numero equivalente a "nro_prod"
        # Metodo criado a fim do objeto utilizado possuir 1 ou mais atributos a serem atualizados
        # Caso o Numero OU o Nome já estejam ocupados, o metodo não atualiza o produto
        # c.execute("SELECT * FROM "+self.estoque_nome+" WHERE nome=? OR numero=? ",(self.nome,self.numero))
        c.execute("SELECT * FROM [" + self.estoque_nome + "] WHERE numero=? ", (self.numero,))
        check = c.fetchone()
        if not check or int(self.numero) == int(nro_prod):
            c.execute("SELECT * FROM [" + self.estoque_nome + "] WHERE nome=? ", (self.nome,))
            check = c.fetchone()
            if not check or check[0] == nro_prod:
                if self.numero and self.nome and self.preço and self.quantidade:
                    c.execute(
                        "UPDATE [" + self.estoque_nome + "] SET numero=?, nome=?, preço=?, quantidade=?  WHERE numero=?",
                        (self.numero, self.nome, self.preço, self.quantidade, nro_prod))
                    conn.commit()

    def remover_produto(self):

        # Remove o produto de sua tabela/estoque correspondente
        with conn:
            c.execute("DELETE FROM [" + self.estoque_nome + "] WHERE numero=?", (self.numero,))


app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def teste():
    repeat = Estoque.mostrar_estoques()
    tam = len(repeat)
    if request.method == "POST":
        #Confere se algum estoque foi deletado e deleta
        for i in range(tam):
            repeat[i]
            for re in repeat:    
                if str(re[1]) in request.form:
                    estoque = re[1]
                    Estoque.remover_estoque(str(estoque))
        #Confere se algum estoque foi adicionado e adiciona
        if "add" in request.form:
            stock = Estoque(request.form.get('novo_estoque'))
            Estoque.criar_tabela(stock)
    
    lista = []
    repeat = Estoque.mostrar_estoques()
    for re in repeat:
        lista.append(re[1])
    return render_template('home.html', len=len(lista), repeat=lista)


@app.route("/estoque", methods=['GET', 'POST'])
def pag_estoque():
    # Metodos Get e Post para manter o nome do estoque na pagina
    if request.method == "GET":
        estoque_info = request.args.get('info')
    elif request.method == "POST":
        estoque_info = request.form["nome_estoque"]
    estoque = Estoque(estoque_info)
    estoque.criar_tabela()
    if request.method == "POST":
        # Checando se o Botão "Atualizar Valores" foi pressionado
        if "atualizar" in request.form:
            # Função para Atualizar a tabela
            w = 0
            for prods in estoque.mostrar_estoque():
                z = str(w)
                prod = Produto(request.form["numero" + z], request.form["nome" + z], request.form["quantidade" + z],
                            request.form["preço" + z], estoque.estoque)
                prod.alterar_produto(prods[0])
                w = w + 1
            # Função para Adicionar novo produto
            prodnovo = Produto(request.form["numeron"], request.form["nomen"], request.form["preçon"],
                            request.form["quantidaden"], estoque.estoque)
            prodnovo.produto_novo()
        # Função para Deletar um produto do estoque
        else:
            z = 2
            for produto in estoque.mostrar_estoque():
                y = str(z)
                #Se um botao de deletar foi pressionado
                if y in request.form:
                    del_produto = Produto(produto[0], produto[1], produto[2], produto[3], estoque.estoque)
                    del_produto.remover_produto()
                z = z + 1

    # Função para criar os nomes ( começando por 0) das informações para o request_form
    prod = str(estoque.mostrar_estoque()).translate({ord(c): '' for c in "[]()'"})
    prod = list(prod.split(","))

    li_li_tup = []
    y = []
    s = ["numero", "nome", "preço", "quantidade"]
    z = 0
    k = 0
    for info in prod:
        j = str(k)
        tup = (s[z] + j, info)
        y.append(tup)
        if z == 3:
            k = k + 1
            li_li_tup.append(y)
            y = []
        z = (z + 1) % 4
    return render_template('estoque.html', li_li_tup=li_li_tup, estoque=estoque.estoque)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)