from flask import Flask, render_template, url_for, flash, redirect, request
import sqlite3
from datetime import datetime

conn = sqlite3.connect('teste.db', check_same_thread=False)
conn.execute("PRAGMA foreign_keys = 1")
c = conn.cursor()

#Cria a tabela com os estoques
c.execute("""CREATE TABLE IF NOT EXISTS Estoques(
    codEstoque INTEGER PRIMARY KEY NOT NULL,
    nome TEXT NOT NULL
)""")

conn.commit()

#Cria a tabela para as sessões
c.execute("""CREATE TABLE IF NOT EXISTS Sessoes(
            receita REAL NOT NULL,
            hora_ini TEXT NOT NULL,
            hora_fim TEXT NOT NULL,
            estoque INTEGER NOT NULL
            FOREIGN KEY (estoque) REFERENCES Estoques(codEstoque) ON DELETE CASCADE
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
            preço REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            estoque INTEGER NOT NULL,
            FOREIGN KEY (estoque) REFERENCES Estoques(codEstoque) ON DELETE CASCADE
            )""")

    @staticmethod
    def remover_estoque(nome_estoque):
        # Recebe o nome do estoque
        # Remove o estoque do Banco e os produtos contidos nesse estoque
        with conn:
            c.execute("DELETE FROM Estoques WHERE nome=?", (nome_estoque,))
        with conn:
            c.execute("DROP TABLE [IF EXISTS] ["+nome_estoque+"]")

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

    @staticmethod
    def cod_estoque(nome):
        # retorna a chave do estoque
        c.execute("SELECT * FROM Estoques WHERE nome = ?", ( nome,))
        lista = c.fetchone()
        return lista[0]


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

class Sessão:

    def __init__(self, estoque_nome, hora_ini, receita = 0, hora_fim = 0, ):
        self.receita = receita
        self.hora_ini = hora_ini
        self.hora_fim = hora_fim
        self.estoque_nome = estoque_nome

    def sessao_nova (self):
        # Insere a sessão na tabela de sessões e cria uma tabela para os produtos vendidos   
        with conn:
            c.execute("INSERT INTO Sessoes VALUES (?, ?, ?, ?)", ( self.receita, self.hora_ini, 
                                                                  self.hora_fim, Estoque.cod_estoque(self.estoque_nome)))
            conn.commit()
        with conn:
            c.execute("""CREATE TABLE IF NOT EXISTS [""" + self.estoque_nome + """_vendidos](
            numero INTEGER NOT NULL,
            nome TEXT NOT NULL,
            preço REAL NOT NULL,
            quantidade INTEGER NOT NULL
            )""")

    def adicionar_receita (self, valor):
        cod = Estoque.cod_estoque(self.estoque_nome)
        c.execute("SELECT receita FROM Sessoes WHERE estoque=? ", ( cod,))
        check = c.fetchone()
        x = check[0]
        x = x + valor
        c.execute("UPDATE Sessoes SET receita=? WHERE estoque=?",( x, cod))
        conn.commit()
    
    def adicionar_hora_fim (self, hora):
        c.execute("UPDATE Sessoes SET hora_fim=? WHERE estoque=?",( hora, Estoque.cod_estoque(self.estoque_nome)))
        conn.commit()

    def fechar_sessao (self):
        with conn:
            c.execute("DELETE FROM Sessoes WHERE estoque=?", (Estoque.cod_estoque(self.estoque_nome),))
        with conn:
            c.execute("DROP TABLE [IF EXISTS] ["+self.estoque_nome+"_vendidos]")



class Prod_Vendido:

    def __init__(self, numero, nome, quantidade, preço, estoque_nome):
            self.numero = numero
            self.nome = nome
            self.quantidade = quantidade
            self.preço = preço
            self.estoque_nome = estoque_nome

    
    def vendido(self):
        c.execute("SELECT numero FROM [" + self.estoque_nome + "_vendidos] WHERE numero=? ",
                                                             (self.estoque_nome,self.numero))
        check = c.fetchone()
        if check:
            c.execute("SELECT quantidade FROM [" + self.estoque_nome + "_vendidos] WHERE numero=? ", 
                                                                    (self.estoque_nome,self.numero))
            check = c.fetchone()
            x = check[0]
            x = x + self.quantidade
            c.execute("UPDATE [" + self.estoque_nome + "_vendidos] SET quantidade=?  WHERE numero=?",
                                                                    (self.estoque_nome, x, self.numero))
            conn.commit()
        else:
            c.execute("INSERT INTO [" + self.estoque_nome + "_vendidos] VALUES (?, ?, ?, ?)", (self.numero, self.nome,
                                                                                           self.preço, self.quantidade))
            conn.commit()






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
    # Checando de o Botão " Vendas" foi pressionado
    if "vendas" in request.form:
        return redirect(url_for('pag_vendas',info=estoque.estoque))
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



@app.route("/vendas", methods=['GET','POST'])
def pag_vendas():
    if request.method == "GET":
        estoque_info = request.args.get('info')
        estoque = Estoque(estoque_info)
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

        #Cria 2 tabelas correspondentes ao estoque, 1 para  Sessão/Relatório, 1 para o Carrinho
        nome_car = request.form["nome_estoque"]+"car"
        car = Estoque(nome_car)
        car.criar_tabela() 
        return render_template('vendas.html', li_li_tup=li_li_tup, estoque=estoque.estoque)
    if request.method == "POST":
        if "carrinho" in request.method:
            nome_car = request.form["nome_estoque"]+"car"
            car = Estoque(nome_car)
            car.criar_tabela()
            


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)