// server.js
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const crypto = require('crypto');

const app = express();
app.use(cors());
app.use(bodyParser.json());

let blockchain = [];
let pendingTx = [];
let wallets = {}; // address -> balance
let coinsOnline = {}; // coinId -> ownerAddress

const GAS_FEE = 0.01;
const MIN_WITNESS = 1; // จำนวนเหรียญ AI ที่ต้องยืนยัน

// =================== Functions =====================
function sha256(data){
    return crypto.createHash('sha256').update(data).digest('hex');
}

function createGenesisBlock(){
    const block = {
        index: 0,
        timestamp: new Date().toISOString(),
        transactions: [],
        previousHash: "0",
        hash: "",
        witnesses: []
    };
    block.hash = sha256(JSON.stringify(block));
    blockchain.push(block);
}

function createBlock(transactions, witnesses){
    const block = {
        index: blockchain.length,
        timestamp: new Date().toISOString(),
        transactions,
        previousHash: blockchain[blockchain.length-1].hash,
        witnesses
    };
    block.hash = sha256(JSON.stringify(block));
    blockchain.push(block);
}

// =================== API ===========================
app.post('/createWallet', (req,res)=>{
    const seed = crypto.randomBytes(32).toString('hex');
    const address = sha256(seed).slice(0,40);
    wallets[address] = 0;
    res.json({seed,address});
});

app.get('/balance/:address',(req,res)=>{
    const addr = req.params.address;
    res.json({balance: wallets[addr]||0});
});

app.post('/mint',(req,res)=>{
    const {address, amount} = req.body;
    wallets[address] = (wallets[address]||0) + amount;
    pendingTx.push({id: sha256(Date.now()+address), from:"SYSTEM", to:address, amount, gas:0, time: new Date().toISOString()});
    res.json({status:"minted",balance: wallets[address]});
});

app.post('/send',(req,res)=>{
    const {from,to,amount} = req.body;
    if((wallets[from]||0) < amount+GAS_FEE) return res.status(400).json({error:"ยอดไม่พอ"});
    wallets[from] -= amount+GAS_FEE;
    wallets[to] = (wallets[to]||0) + amount;

    // แจกค่าแก๊สให้ coins online
    const onlineCoins = Object.keys(coinsOnline);
    const share = GAS_FEE / onlineCoins.length;
    onlineCoins.forEach(cid=>{
        const owner = coinsOnline[cid];
        wallets[owner] = (wallets[owner]||0) + share;
    });

    const tx = {id: sha256(Date.now()+from), from,to,amount,gas:GAS_FEE,time:new Date().toISOString()};
    pendingTx.push(tx);

    // ตรวจสอบ witness
    if(onlineCoins.length>=MIN_WITNESS){
        createBlock(pendingTx,onlineCoins.slice());
        pendingTx = [];
    }

    res.json({status:"sent",tx});
});

// รายงาน Blockchain
app.get('/chain',(req,res)=>{
    res.json(blockchain);
});

// รายงาน online coins
app.get('/online',(req,res)=>{
    res.json(coinsOnline);
});

// register coin online
app.post('/coinOnline',(req,res)=>{
    const {coinId, owner} = req.body;
    coinsOnline[coinId] = owner;
    res.json({status:"online"});
});

app.listen(3000,()=>console.log("NXI Blockchain Engine running on port 3000"));
createGenesisBlock();
