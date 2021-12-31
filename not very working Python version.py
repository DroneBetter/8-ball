import sys, pygame, time, math, random
from pygame.locals import *
 
pygame.init()
 
def drawShape(w,h,x,y,colour,shape):
    color=(colour[0],colour[1],colour[2])
    if shape==0:
        surf = pygame.Surface((w, h))
        surf.fill(color)
        rect = surf.get_rect()
        screen.blit(surf, (x, y))
    else:
        pygame.draw.circle(screen, color, (x, y), w/2)

size=[800,600]
black=0,0,0
screen = pygame.display.set_mode((size[0], size[1]))
dims=2
drag=0
FPS=60
gravitationalConstant=min(size)/FPS
#square format: [ [[position,velocity],[position,velocity]], [size,size], mass ]
#call format: square[square][characteristic][dimension?][position or velocity]
squares=[ [ [[random.random()*size[i],0] for i in range(dims)], [40]*2, 10, [int(255*(math.cos((i2/9-i/3)*2*math.pi)+1)/2) for i in range(3)] ] for i2 in range(9)]
 
def reflect(squaro,mirror,nextValue):
    squaro[0]=mirror*2-nextValue
    squaro[1]*=-1

def lineSphereIntersection(line,sphereRadius): #line formatted like square position/velocity list
    #Ask Mathematica whether it can be simplified:
    #(sqrt((x*t+y*u+z*v)^2-(t^2+u^2+v^2)*(x^2+y^2+z^2-r^2))-(x*t+y*u+z*v))/(t^2+u^2+v^2)
    global D
    A=0
    B=0
    C=-sphereRadius**2
    for di in range(dims):
        A+=line[di][1]**2
        B+=line[di][0]*line[di][1]
        C+=line[di][0]**2
    D=B**2-A*C
    if A==0:
        return -1/2**55
    elif D<0:
        return D
    else:
        D=math.sqrt(D)/2
        t1=(D-B)/A
        t2=(-D-B)/A
        if t1<t2 and t1>0:
            t=t1
        else:
            t=t2
        if t>0:
            return t
        else:
            return -1/2**55

def dotProduct(a,b):
    return sum([a[i]*b[i] for i in range(len(a))])

def lineCollision(m1,v1,m2,v2):
    rV=[((m1-m2)*v1+(2*m2)*v2)/(m1+m2),((m2-m1)*v2+(2*m1)*v1)/(m1+m2)]
    return rV

def tangentSphereCollision(spheres,refract,n): #n is refractive index
    dM=0
    differences=[[],[]]
    sphereVs=[[],[]]
    for di in range(dims):
        for i in range(2):
            differences[i].append(spheres[1][0][di][i]-spheres[0][0][di][i])
        dM+=differences[0][di]**2
    dM=math.sqrt(dM)
    if spheres[1][2]==0:
        #for raytracing
        Ca=2*dotProduct(differences[1],differences[0])/(dM**2)
        collisionDeltaV=[Ca*differences[0][di] for di in range(dims)]
        discriminant=1-((n**2)*(1-Ca**2))
        return [spheres[1][0][di][1]+n*(differences[0][di]-2*collisionDeltaV[di])-(velocityDifferences[di]*sqrt(discriminant)) if (refract==1 and discriminant>0) else spheres[1][0][i][1]+collisionDeltaV[i]-2*spheres[0][0][i][1] for di in range(dims)]
    else:
        Ca=[dotProduct([spheres[i][0][di][1] for di in range(dims)],differences[0])/dM for i in range(2)]
        rV=lineCollision(spheres[0][2],Ca[0],spheres[1][2],Ca[1])
        return [[spheres[i][0][di][1]+(rV[i]-Ca[i])*differences[0][di]/dM for di in range(dims)] for i in range(2)]

def proceedTime(timeToProceed):
    for i in range(len(squares)):
        for di in range(dims):
            squares[i][0][di][0]+=squares[i][0][di][1]
    global timeProceeded
    timeProceeded+=timeToProceed

def physics():
    for i in range(len(squares)):
        if drag>0:
            absVel=math.sqrt(sum([squares[i][0][di][1]**2 for di in range(dims)])) #each dimension's deceleration from drag is its magnitude as a component of the unit vector of velocity times absolute velocity squared, is actual component times absolute velocity.
            for di in range(dims):
                squares[i][0][di][1]*=1-absVel*drag #air resistance
    for i in range(len(squares)-1):
        for i2 in range(i+1,len(squares)):
            differences=[squares[i2][0][di][0]-squares[i][0][di][0] for di in range(dims)]
            gravity=gravitationalConstant/math.sqrt(sum([differences[di]**2 for di in range(dims)])**3)
            for di in range(dims):
                squares[i][0][di][1]+=differences[di]*gravity*squares[i2][2]
                squares[i2][0][di][1]-=differences[di]*gravity*squares[i][2]
    cycles=0
    global timeProceeded
    timeProceeded=0
    while cycles==0 or len(candidates)>0:
        cycles+=1
        timeToProceed=1-timeProceeded
        candidates=[]
        for i in range(len(squares)):
            for di in range(dims):
                squaro=squares[i][0][di]
                nextValue=squaro[0]+squaro[1]
                mirror=squares[i][1][di]
                if nextValue<mirror:
                    t=(mirror-squaro[0])/squaro[1]
                else:
                    mirror=size[di]
                    if nextValue>mirror:
                        t=(mirror-squaro[0])/squaro[1]
                    else:
                        t=-1
                if not (t<0 or t>timeToProceed):
                    timeToProceed=t
                    candidates=[i]
                    canDi=di #delicious
            for i2 in range(i+1,len(squares)):
                t=lineSphereIntersection([[squares[i2][0][di][der]-squares[i][0][di][der] for der in range(2)] for di in range(dims)], squares[i2][1][0]+squares[i][1][0])
                if not (t<0 or t>timeToProceed):
                    timeToProceed=t
                    candidates=[i,i2]
        proceedTime(timeToProceed)
        if len(candidates)==1:
            squares[candidates[0]][0][canDi][1]*=-1
        elif len(candidates)==2:
            if 0==1: #testing
                for di in range(dims):
                        squares[candidates[i]][0][di][1]*=-1
            else:
                resVel=tangentSphereCollision([squares[candidates[i]] for i in range(2)],0,0)
                for i in range(2):
                    for di in range(dims):
                        squares[candidates[i]][0][di][1]=resVel[i][di]

while 1:
    physics()
    screen.fill(black)
    for i in range(len(squares)):
        drawShape(squares[i][1][0]+20,squares[i][1][1]+20,squares[i][0][0][0]-20,squares[i][0][1][0]-20,squares[i][3],1)
    pygame.display.flip()
    time.sleep(1/FPS)
