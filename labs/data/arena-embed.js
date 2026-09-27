(function(){
var d=document,s=d.createElement('script');
s.textContent=`
fetch('http://147.224.38.131:4044/leaderboard').then(r=>r.json()).then(d=>{
var lb=d.leaderboard||d;
var html='<div style="font-family:monospace;background:#0a0a0f;color:#d8d8ec;padding:16px;border-radius:8px;max-width:400px">';
html+='<h3 style="color:#e94560;margin:0 0 8px;font-size:14px">🏟️ Arena Leaderboard</h3>';
lb.slice(0,5).forEach((a,i)=>{
var colors=['#FFD700','#C0C0C0','#CD7F32','#d8d8ec','#d8d8ec'];
html+='<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #1c1c35;font-size:12px;color:'+colors[i]+'">';
html+='<span>#'+(i+1)+' '+a.name+'</span><span>'+Math.round(a.rating)+' ELO</span></div>';
});
html+='</div>';
var c=document.getElementById('arena-leaderboard')||document.body;
c.innerHTML=html;
}).catch(()=>{});
`;
d.head.appendChild(s);
})();
