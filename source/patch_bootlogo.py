"""Replace only existing same-size logo resources and their hashes in a known FIT."""
import hashlib
import struct

def patch(original, logo):
    b=bytearray(original)
    assert len(b)==16777216
    hdr=struct.unpack_from('>10I',b);assert hdr[0]==0xd00dfeed
    strings=b[hdr[3]:hdr[3]+hdr[8]];pos=hdr[2];stack=[];props={}
    while True:
        token=struct.unpack_from('>I',b,pos)[0];pos+=4
        if token==1:
            end=b.index(0,pos);stack.append(b[pos:end].decode());pos=(end+4)&~3
        elif token==2:stack.pop()
        elif token==3:
            size,index=struct.unpack_from('>II',b,pos);pos+=8
            name=strings[index:strings.index(0,index)].decode();props[('/'.join(stack),name)]=(pos,size);pos=(pos+size+3)&~3
        elif token==9:break
        elif token!=4:raise ValueError('Invalid FIT token')
    def value(path,name):
        p,n=props[path,name];return bytes(b[p:p+n])
    def integer(path,name):return int.from_bytes(value(path,name),'big')
    for name in ['fdt','kernel','resource']:
        p='/images/'+name;start=integer(p,'data-position');size=integer(p,'data-size')
        assert hashlib.sha256(b[start:start+size]).digest()==value(p+'/hash','value')
    r=integer('/images/resource','data-position');size=integer('/images/resource','data-size')
    assert b[r:r+4]==b'RSCE';count=struct.unpack_from('<I',b,r+12)[0];assert count==3
    allowed=[];names=[]
    for i in range(count):
        e=r+512*(i+1);name=bytes(b[e+4:e+224]).split(b'\0')[0].decode()
        hs,offset,n=struct.unpack_from('<III',b,e+256);start=r+512*offset
        assert hs==20 and hashlib.sha1(b[start:start+n]).digest()==bytes(b[e+224:e+244])
        if name in ('logo.bmp','logo_kernel.bmp'):
            assert len(logo)==n and logo[:54]==bytes(b[start:start+54])
            b[start:start+n]=logo;b[e+224:e+244]=hashlib.sha1(logo).digest()
            allowed.extend([(start,start+n),(e+224,e+244)]);names.append(name)
    assert len(names)==2
    p,n=props['/images/resource/hash','value'];assert n==32
    b[p:p+n]=hashlib.sha256(b[r:r+size]).digest();allowed.append((p,p+n))
    assert all(any(start<=i<end for start,end in allowed) for i,(a,z) in enumerate(zip(original,b)) if a!=z)
    return bytes(b)
