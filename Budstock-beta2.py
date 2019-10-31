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
            estoque INTEGER NOT NULL,
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
            c.execute("DROP TABLE IF EXISTS ["+nome_estoque+"]")

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

    def __init__(self, numero, nome, preço, quantidade, estoque_nome):

        # O ultimo atributo recebe o nome do estoque ao qual o produto pertence
        self.numero = numero
        self.nome = nome
        self.preço = preço
        self.quantidade = quantidade
        self.estoque_nome = estoque_nome

    def produto_novo(self):

        # Insere o produto na tabela correspondente ao seu estoque
        # Caso o Numero OU o Nome já estejam ocupados, o metodo não insere o produto
        c.execute("SELECT * FROM [" + self.estoque_nome + "] WHERE nome=? OR numero=? ", (self.nome, self.numero))
        check = c.fetchone()
        if not check:
            if self.numero and self.nome and self.preço and self.quantidade:
                c.execute("SELECT * FROM Estoques WHERE nome = ?", (self.estoque_nome,))
                lista = c.fetchone()
                c.execute("INSERT INTO [" + self.estoque_nome + "] VALUES (?, ?, ?, ?, ?)", (self.numero, self.nome,self.preço, self.quantidade,lista[0]))
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

class Sessao:

    def __init__(self, estoque_nome, hora_ini, receita = 0, hora_fim = "0/0/0", ):
        self.receita = receita
        self.hora_ini = hora_ini
        self.hora_fim = hora_fim
        self.estoque_nome = estoque_nome

    def sessao_nova (self):
        # Insere a sessão na tabela de sessões e cria uma tabela para os produtos vendidos
        # Se a sessão nao foi encerrada, os dados antigos permanecerão
        cod = Estoque.cod_estoque(self.estoque_nome)
        c.execute("SELECT * FROM Sessoes WHERE estoque=? ", (cod,))
        check = c.fetchone()
        print("printando check:")
        print(check)
        if not check:
            with conn:
                c.execute("INSERT INTO Sessoes VALUES (?, ?, ?, ?)", ( self.receita, self.hora_ini, 
                                                                  self.hora_fim, cod))
        with conn:
            c.execute("""CREATE TABLE IF NOT EXISTS [""" + self.estoque_nome + """_vendidos](
                numero INTEGER NOT NULL,
                nome TEXT NOT NULL,
                preço REAL NOT NULL,
                quantidade INTEGER NOT NULL
                )""")

    @staticmethod
    def adicionar_receita (estoque, valor):
        cod = Estoque.cod_estoque(estoque)
        c.execute("SELECT receita FROM Sessoes WHERE estoque=? ", ( cod,))
        check = c.fetchone()
        x = check[0]
        x = x + valor
        c.execute("UPDATE Sessoes SET receita=? WHERE estoque=?",( x, cod))
        conn.commit()
    
    @staticmethod
    def adicionar_hora_fim (estoque, hora):
        c.execute("UPDATE Sessoes SET hora_fim=? WHERE estoque=?",( hora, Estoque.cod_estoque(estoque)))
        conn.commit()

    @staticmethod
    def get_vendidos (estoque):
        c.execute("SELECT * FROM [" + estoque + "_vendidos] ")
        check = c.fetchall()
        return check

    @staticmethod
    def get_sessao (estoque):
        c.execute("SELECT receita,hora_ini,hora_fim FROM Sessoes WHERE estoque=? ",(Estoque.cod_estoque(estoque),))
        check = c.fetchall()
        return check[0]


    @staticmethod
    def fechar_sessao (estoque):
        with conn:
            c.execute("DELETE FROM Sessoes WHERE estoque=?", (Estoque.cod_estoque(estoque),))
        with conn:
            c.execute("DROP TABLE  ["+ estoque +"_vendidos]")



class Prod_Vendido:

    def __init__(self, numero, nome, quantidade, preço, estoque_nome):
            self.numero = numero
            self.nome = nome
            self.quantidade = quantidade
            self.preço = preço
            self.estoque_nome = estoque_nome

    
    def vendido(self):
        c.execute("SELECT numero FROM [" + self.estoque_nome + "_vendidos] WHERE numero=? ",
                                                             (self.numero,))
        check = c.fetchone()
        if check:
            c.execute("SELECT quantidade FROM [" + self.estoque_nome + "_vendidos] WHERE numero=? ", 
                                                                    (self.numero,))
            check = c.fetchone()
            x = check[0]
            x = x + int(self.quantidade)
            c.execute("UPDATE [" + self.estoque_nome + "_vendidos] SET quantidade=?  WHERE numero=?",
                                                                    ( x, self.numero))
            conn.commit()
        else:
            c.execute("INSERT INTO [" + self.estoque_nome + "_vendidos] VALUES (?, ?, ?, ?)", (self.numero, self.nome,
                                                                                           self.preço, self.quantidade))
            conn.commit()
        c.execute("SELECT quantidade FROM [" + self.estoque_nome + "] WHERE numero=? ",
                                                             (self.numero,))
        check = c.fetchone()
        x = check[0]
        x = x - int(self.quantidade)
        c.execute("UPDATE [" + self.estoque_nome + "] SET quantidade=?  WHERE numero=?",
                                                                    ( x, self.numero))
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
                prod = Produto(request.form["numero" + z], request.form["nome" + z], request.form["preço" + z],
                            request.form["quantidade" + z], estoque.estoque)
                prod.alterar_produto(prods[0])
                w = w + 1
            # Função para Adicionar novo produto
            prodnovo = Produto(request.form["numeron"], request.form["nomen"], request.form["preçon"],
                            request.form["quantidaden"], estoque.estoque)
            print("valores inseridos")
            print(prodnovo.numero,prodnovo.nome,prodnovo.preço,prodnovo.quantidade)
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
    print("estoque:")
    print(prod)

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

        #Insere a sessao na tabela de Sessoes e cria uma tabela Prod_vendidos para a sessão
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
        print(data_hora)
        sessao = Sessao(estoque_info, data_hora)
        sessao.sessao_nova()


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
        
        return render_template('vendas.html', li_li_tup=li_li_tup, estoque=estoque.estoque)
                   

@app.route("/carrinho", methods=['POST'])
def pag_carrinho():
    if "carrinho" in request.form:
        # Função para enviar os produtos selecionados para o carrinho usando dicionario
        dic ={}
        li_dic = []
        s = ["numero", "nome", "preço", "quantidade"]
        z = 0
        while "numero"+str(z) in request.form:
            for k in range(4):
                dic[s[k]+str(z)] = request.form[s[k]+str(z)]
            li_dic.append(dic)
            dic = {}
            z = z+1
        print(li_dic)
        return render_template('carrinho.html', li_dic = li_dic, estoque = request.form["nome_estoque"] )
    elif "confirmar" in request.form:
        # Função para confirmar a venda dos produtos, retirar quantidade do estoque e adicionar na tabela _vendidos
        estoque = Estoque(request.form["nome_estoque"])
        prod_v = Prod_Vendido(0,"0",0,0,estoque.estoque)
        z = 0
        val = 0
        while "numero"+str(z) in request.form:
            prod_v.numero = request.form["numero"+str(z)]
            prod_v.nome = request.form["nome"+str(z)]
            prod_v.preço = request.form["preço"+str(z)]
            prod_v.quantidade = request.form["quantidade"+str(z)]
            prod_v.vendido()
            val = val + float(prod_v.preço)*int(prod_v.quantidade)
            z = z+1
        Sessao.adicionar_receita(estoque.estoque, val)

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
        
        return render_template('vendas.html', li_li_tup=li_li_tup, estoque=estoque.estoque)
    elif "encerrar" in request.form:
        return redirect(url_for('pag_relatorio',info=request.form["nome_estoque"]))

@app.route("/relatorio", methods=['GET'])
def pag_relatorio():
    if request.method == 'GET':
        estoque_info = request.args.get('info')
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
        Sessao.adicionar_hora_fim(estoque_info, data_hora)
        li_li = Sessao.get_vendidos(estoque_info)
        sess = Sessao.get_sessao(estoque_info)
        Sessao.fechar_sessao(estoque_info)
        return render_template('sessao_fim.html', receita = sess[0], hora_ini = sess[1], hora_fim = sess[2], li_li = li_li, estoque = estoque_info)
            







if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)