import assert from "node:assert"
import plugin, { ehLimite, proximoModelo, separar } from "./opencode-gratis-sempre.js"
assert(ehLimite("429 Too Many Requests")); assert(ehLimite("Rate limit exceeded")); assert(ehLimite("You exceeded your quota"))
assert(!ehLimite("File not found")); assert(!ehLimite("syntax error in line 3"))
const L = ["a/1","a/2","a/3"]
assert.equal(proximoModelo(L,"a/1",{}),"a/2")
assert.equal(proximoModelo(L,"a/3",{}),"a/1")
assert.equal(proximoModelo(L,"a/1",{"a/2":Date.now()+1e6}),"a/3")
assert.equal(proximoModelo(L,"a/1",{"a/2":Date.now()+1e6,"a/3":Date.now()+1e6}),null)
assert.deepEqual(separar("9router/kgw/x:free"),{providerID:"9router",modelID:"kgw/x:free"})
// simulacao de ponta a ponta
const chamadas=[], avisos=[]
const client={
  tui:{showToast:async({body})=>avisos.push(body.message)},
  app:{log:async()=>{}},
  session:{
    messages:async()=>({data:[{info:{role:"user"},parts:[{type:"text",text:"faz isso"}]},{info:{role:"assistant"},parts:[]}]}),
    prompt:async(a)=>chamadas.push(a),
  },
}
const p = await plugin.setup({client,directory:"D:/Projetos/PesquisaIA"})
const ev = {type:"message.updated",properties:{info:{role:"assistant",sessionID:"s1",providerID:"opencode",modelID:"deepseek-v4.1-flash-free",error:{name:"APIError",data:{message:"429 rate limit",statusCode:429}}}}}
await p.event({event:ev}); await p.event({event:ev})
assert.equal(chamadas.length,1,"deve ignorar o evento duplicado")
assert.equal(chamadas[0].body.parts[0].text,"faz isso")
assert.notEqual(chamadas[0].body.model.modelID,"deepseek-v4.1-flash-free")
assert(avisos.length>=1)
await p.event({event:{type:"message.updated",properties:{info:{role:"assistant",sessionID:"s2",error:{name:"X",message:"arquivo nao existe"}}}}})
assert.equal(chamadas.length,1,"erro comum nao troca de modelo")
console.log("TODOS OS TESTES DO PLUGIN PASSARAM; novo modelo:", chamadas[0].body.model)
