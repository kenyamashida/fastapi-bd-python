<div align="center">
    <h1>🚀 CRUD API de Usuários com FastAPI e MongoDB</h1>
    <p>API RESTful completa desenvolvida em Python para gerenciamento de usuários.</p>
</div>

<hr>

<h2>📝 Descrição do Projeto</h2>

<p>
    Esta aplicação implementa as operações CRUD (Create, Read, Update, Delete) completas. Utiliza o framework <b>FastAPI</b> para alta performance assíncrona e o <b>MongoDB Atlas</b> (via driver <b>Motor</b>) para persistência de dados NoSQL.
</p>
<p>
    O deploy do serviço foi realizado com sucesso na plataforma <b>Render</b>.
</p>

<h3>🔑 Tecnologias Utilizadas</h3>

<table width="100%">
    <thead>
        <tr>
            <th>Tecnologia</th>
            <th>Função</th>
            <th>Observação</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b>Python</b></td>
            <td>Linguagem base.</td>
            <td>Versão 3.10+</td>
        </tr>
        <tr>
            <td><b>FastAPI</b></td>
            <td>Framework API (Alta performance).</td>
            <td>Gera documentação automática (Swagger UI).</td>
        </tr>
        <tr>
            <td><b>Pydantic (v2)</b></td>
            <td>Validação de Dados.</td>
            <td>Garante que os modelos de entrada e saída estão corretos.</td>
        </tr>
        <tr>
            <td><b>MongoDB / Motor</b></td>
            <td>Banco de Dados (Assíncrono).</td>
            <td>Driver oficial para operações não-bloqueantes.</td>
        </tr>
        <tr>
            <td><b>Render</b></td>
            <td>Deploy / Hospedagem.</td>
            <td>Plataforma moderna para CI/CD.</td>
        </tr>
    </tbody>
</table>

<hr>

<h2>💡 Funcionalidades da API (Endpoints)</h2>

<table width="100%">
    <thead>
        <tr>
            <th>Método</th>
            <th>Endpoint</th>
            <th>Descrição</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><code>POST</code></td>
            <td><code>/users/</code></td>
            <td><b>CREATE:</b> Cria um novo usuário (nome, idade).</td>
        </tr>
        <tr>
            <td><code>GET</code></td>
            <td><code>/users/</code></td>
            <td><b>READ ALL:</b> Retorna a lista completa de todos os usuários.</td>
        </tr>
        <tr>
            <td><code>GET</code></td>
            <td><code>/users/{id}</code></td>
            <td><b>READ BY ID:</b> Busca um usuário específico pelo ID do MongoDB.</td>
        </tr>
        <tr>
            <td><code>PUT</code></td>
            <td><code>/users/{id}</code></td>
            <td><b>UPDATE:</b> Modifica os dados de um usuário existente (requer o ID).</td>
        </tr>
        <tr>
            <td><code>DELETE</code></td>
            <td><code>/users/{id}</code></td>
            <td><b>DELETE:</b> Remove um usuário do banco de dados (Status 204).</td>
        </tr>
        <tr>
            <td><code>POST</code></td>
            <td><code>/users/upload/</code></td>
            <td><b>Extra:</b> Inserção em massa via upload de arquivo CSV.</td>
        </tr>
    </tbody>
</table>

<hr>

<h2>🛠️ Configuração e Execução Local</h2>

<h3>1. Variáveis de Ambiente</h3>

É necessário um arquivo <code>.env</code> na raiz do projeto com a URL de conexão do MongoDB Atlas.

<pre>
# .env
MONGO_URI="mongodb+srv://&lt;USUARIO&gt;:&lt;SENHA&gt;@&lt;CLUSTER_URL&gt;/?retryWrites=true&amp;w=majority"
DB_NAME="fastapi_users_db"
COLLECTION_NAME="users"
</pre>

<h3>2. Passos para Inicialização</h3>

<p>Instale as dependências listadas em <code>requirements.txt</code> e inicie o servidor:</p>

<pre>
# Instalação (dentro do ambiente virtual)
pip install -r requirements.txt

# Inicia o servidor em modo de desenvolvimento
python -m uvicorn main:app --reload
</pre>

<p>A documentação interativa estará acessível em <a href="http://127.0.0.1:8000/docs">http://127.0.0.1:8000/docs</a>.</p>

<hr>

<h2>🚢 Detalhes do Deploy (Render)</h2>

<p>O Render é configurado para deploy contínuo, utilizando:</p> <ul> <li><b><code>Procfile</code>:</b> Define o comando de inicialização (<code>web: uvicorn main:app --host 0.0.0.0 --port $PORT</code>).</li> <li><b>Variáveis Secretas:</b> A variável <code>MONGO_URI</code> está definida como um segredo no painel do Render.</li> <li><b>Acesso de Rede:</b> O cluster MongoDB Atlas deve permitir conexões de <code>0.0.0.0/0</code> para o Render conseguir conectar.</li> </ul>

<hr>

<h2>✍️ Kenyamashida</h2>