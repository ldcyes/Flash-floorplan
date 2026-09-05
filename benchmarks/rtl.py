"""Original synthetic RTL and independent cycle-vector generators. MIT, Liangdacheng.
Crossbar broadcasts; Benes routes permutations: they are not functionally identical.
"""
import math, random

def fabric(kind,n,w):
    k=n.bit_length()-1
    controls=n*k if kind=='crossbar' else (2*k-1)*n//2
    text=f'module top(input clk, input [{n*w-1}:0] din, input [{controls-1}:0] sel, output reg [{n*w-1}:0] dout);\n'
    if kind=='crossbar':
        text+=f'genvar o; generate for(o=0;o<{n};o=o+1) begin always @(posedge clk) dout[o*{w}+:{w}] <= din[sel[o*{k}+:{k}]*{w}+:{w}]; end endgenerate\nendmodule\n'
    else:
        text+=f'wire [{n*w-1}:0] comb; benes #({n},{w}) b(din,sel,comb); always @(posedge clk) dout<=comb; endmodule\n'
        text+='''module benes #(parameter N=4,W=8,K=$clog2(N),C=(2*K-1)*N/2)(input [N*W-1:0] din,input [C-1:0] sel,output [N*W-1:0] dout);
 generate if(N==2) begin
  assign dout[W-1:0]=sel[0]?din[2*W-1:W]:din[W-1:0];
  assign dout[2*W-1:W]=sel[0]?din[W-1:0]:din[2*W-1:W];
 end else begin
  localparam SUB=(2*(K-1)-1)*(N/4);
  wire [N/2*W-1:0] up_in,lo_in,up_out,lo_out;
  genvar i; for(i=0;i<N/2;i=i+1) begin
   assign up_in[i*W+:W]=sel[i]?din[(2*i+1)*W+:W]:din[(2*i)*W+:W];
   assign lo_in[i*W+:W]=sel[i]?din[(2*i)*W+:W]:din[(2*i+1)*W+:W];
   assign dout[2*i*W+:W]=sel[N/2+2*SUB+i]?lo_out[i*W+:W]:up_out[i*W+:W];
   assign dout[(2*i+1)*W+:W]=sel[N/2+2*SUB+i]?up_out[i*W+:W]:lo_out[i*W+:W];
  end
  benes #(N/2,W) u(up_in,sel[N/2+:SUB],up_out);
  benes #(N/2,W) l(lo_in,sel[N/2+SUB+:SUB],lo_out);
 end endgenerate
endmodule
'''
    return text,controls

def benes_reference(values,controls):
    n=len(values)
    if n==2: return values[::-1] if controls[0] else values[:]
    half=n//2; sub=(2*int(math.log2(half))-1)*half//2
    up=[];lo=[]
    for i in range(half):
        a,b=values[2*i:2*i+2]
        if controls[i]: a,b=b,a
        up.append(a);lo.append(b)
    up=benes_reference(up,controls[half:half+sub]);lo=benes_reference(lo,controls[half+sub:half+2*sub])
    result=[]
    for i in range(half):
        pair=[up[i],lo[i]]
        result.extend(pair[::-1] if controls[half+2*sub+i] else pair)
    return result

def router(n,w,depth=4):
    return f'''module top(input clk,input rst,input [{n*w-1}:0] din,input [{n*(n.bit_length()-1)-1}:0] dest,input [{n-1}:0] in_valid,output [{n-1}:0] in_ready,output reg [{n*w-1}:0] dout,output reg [{n-1}:0] out_valid,input [{n-1}:0] out_ready);
localparam N={n},W={w},K={n.bit_length()-1};
wire [N*W-1:0] heads; wire [N*K-1:0] targets; wire [N-1:0] nonempty; reg [N-1:0] pop;
reg [K-1:0] rr[0:N-1]; reg [K-1:0] selected[0:N-1];
genvar p; generate for(p=0;p<N;p=p+1) begin
 fifo #(.W(W+K),.D({depth})) f(clk,rst,{{dest[p*K+:K],din[p*W+:W]}},in_valid[p],in_ready[p],{{targets[p*K+:K],heads[p*W+:W]}},nonempty[p],pop[p]);
end endgenerate
integer o,j,k; reg found;
always @* begin
 pop=0; dout=0; out_valid=0; found=0; j=0;
 for(o=0;o<N;o=o+1) begin
  found=0; selected[o]=0;
  for(k=0;k<N;k=k+1) begin
   j=(rr[o]+k)%N;
   if(!found && nonempty[j] && targets[j*K+:K]==o) begin
    found=1; selected[o]=j; out_valid[o]=1; dout[o*W+:W]=heads[j*W+:W];
    if(out_ready[o]) pop[j]=1;
   end
  end
 end
end
integer z;
always @(posedge clk) begin
 for(z=0;z<N;z=z+1) begin
  if(rst) rr[z]<=0;
  else if(out_valid[z] && out_ready[z]) rr[z]<=selected[z]+1'b1;
 end
end
endmodule
module fifo #(parameter W=10,D=4,L=$clog2(D))(input clk,input rst,input [W-1:0] din,input valid,output ready,output [W-1:0] dout,output nonempty,input pop);
reg [W-1:0] mem[0:D-1]; reg [L-1:0] rd,wr; reg [L:0] count;
wire push=valid && ready;
assign nonempty=count!=0;
assign ready=(count<D)||pop;
assign dout=mem[rd];
always @(posedge clk) begin
 if(rst) begin rd<=0; wr<=0; count<=0; end
 else begin
  if(push) begin mem[wr]<=din; wr<=wr+1'b1; end
  if(pop) rd<=rd+1'b1;
  case({{push,pop}}) 2'b10:count<=count+1'b1; 2'b01:count<=count-1'b1; default:count<=count; endcase
 end
end
endmodule
'''

def pack(vals,w): return sum(v<<(i*w) for i,v in enumerate(vals))
def lit(v,b): return f"{b}'h{v:x}"

def testbench(kind,n,w,cycles=256):
    rng=random.Random(7301+n*37+w); bits=n*w;k=n.bit_length()-1
    if kind!='router':
        c=n*k if kind=='crossbar' else (2*k-1)*n//2
        t=f'module tb; reg clk=0; always #5 clk=~clk; reg [{bits-1}:0] din; reg [{c-1}:0] sel; wire [{bits-1}:0] dout; top dut(clk,din,sel,dout); initial begin\n'
        for i in range(cycles):
            vals=[rng.getrandbits(w) for _ in range(n)];control=rng.getrandbits(c)
            out=[vals[(control>>(o*k))&(n-1)] for o in range(n)] if kind=='crossbar' else benes_reference(vals,[(control>>a)&1 for a in range(c)])
            t+=f'@(negedge clk); din={lit(pack(vals,w),bits)};sel={lit(control,c)};@(posedge clk);#1;if(dout!=={lit(pack(out,w),bits)}) $fatal(1,"vector {i}");\n'
        t+=f'$display("PASS {kind} N={n} W={w} cycles={cycles}");$finish;end endmodule\n'
        return t
    t=f'module tb;reg clk=0;always #5 clk=~clk;reg rst=1;reg [{bits-1}:0] din=0;reg [{n*k-1}:0] dest=0;reg [{n-1}:0] in_valid=0,out_ready=0;wire [{n-1}:0] in_ready,out_valid;wire [{bits-1}:0] dout;top dut(clk,rst,din,dest,in_valid,in_ready,dout,out_valid,out_ready);initial begin repeat(2) @(posedge clk);@(negedge clk);rst=0;\n'
    qs=[[] for _ in range(n)];rr=[0]*n
    for cycle in range(cycles+64):
        vals=[rng.getrandbits(w) for _ in range(n)]; dst=[rng.randrange(n) for _ in range(n)]
        valid=[int(rng.random()<.8) if cycle<cycles else 0 for _ in range(n)]
        ready=[int(rng.random()<.65) if cycle<cycles else 1 for _ in range(n)]
        outs=[0]*n;ov=[0]*n;pop=[False]*n;selected=[None]*n
        for o in range(n):
            for a in range(n):
                p=(rr[o]+a)%n
                if qs[p] and qs[p][0][1]==o:
                    outs[o]=qs[p][0][0];ov[o]=1;selected[o]=p;pop[p]=bool(ready[o]);break
        ir=[int(len(qs[p])<4 or pop[p]) for p in range(n)]
        mask=pack([(1<<w)-1 if x else 0 for x in ov],w)
        t+=f'din={lit(pack(vals,w),bits)};dest={lit(pack(dst,k),n*k)};in_valid={lit(pack(valid,1),n)};out_ready={lit(pack(ready,1),n)};#1;'
        t+=f'if(in_ready!=={lit(pack(ir,1),n)} || out_valid!=={lit(pack(ov,1),n)} || (dout & {lit(mask,bits)})!=={lit(pack(outs,w)&mask,bits)}) $fatal(1,"router cycle {cycle}");@(posedge clk);#1;@(negedge clk);\n'
        for o,p in enumerate(selected):
            if p is not None and ready[o]: rr[o]=(p+1)%n
        for p in range(n):
            if pop[p]:qs[p].pop(0)
            if ir[p] and valid[p]:qs[p].append((vals[p],dst[p]))
    assert not any(qs),'drain failed'
    t+=f'$display("PASS router N={n} W={w} cycles={cycles+64}");$finish;end endmodule\n'
    return t
