import sys, pygame, math, random
from pygame.locals import *
clock=pygame.time.Clock()
 
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
perspectiveMode=0
projectionMode=1
gravitationalConstant=min(size)/FPS

#square format: [ [[position,velocity],[position,velocity]], [size,size], mass ]
#call format: square[square][characteristic][dimension?][position or velocity]
squares=[ [ [[random.random()*size[i],0] for i in range(dims)], [40]*2, 10, [int(255*(math.cos((i2/9-i/3)*2*math.pi)+1)/2) for i in range(3)] ] for i2 in range(9)]

cameraPosition=[0]*dims
cameraOrientation=[[1]+[0]*3]*2

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


def quaternionMultiply(a,b):
    return [a[0]*b[0]-a[1]*b[1]-a[2]*b[2]-a[3]*b[3],a[0]*b[1]+a[1]*b[0]+a[2]*b[3]-a[3]*b[2],a[0]*b[2]-a[1]*b[3]+a[2]*b[0]+a[3]*b[1],a[0]*b[3]+a[1]*b[2]+a[2]*b[1]+a[3]*b[0]]

def quaternionConjugate(q):
    return [q[0]]+[-q[i+1] for i in range(len(q)-1)]

def rotateByLocalGimbals(q,g):
    magnitude=math.sqrt(sum([i**2 for i in g]))
    return quaternionMultiply([math.cos(magnitude),[i*math.sin(magnitude)/magnitude for i in g]],q)

def rotate2D(vector,angle):
    return [sum([vector[j]*math.cos(math.pi/2*(j-i)) for j in range(2)]) for i in range(2)]

def projectSpaceToScreen(v,sR): #Outputs list of two coordinates
    if projectionMode==0: #The strange mode which stretches each hemisphere to a square
        return [math.atan2(v[i],v[2]) for i in range(2)]
    elif projectionMode<5: # Azimuthal ones
        newRadius=0
        smagnitude=sum([v[i]**2 for i in range(2)])
        magnitude=math.atan2(math.sqrt(smagnitude,v[2]))
        if projectionMode==2: #Equi-area (equidistant is projectionMode 1)
            magnitude=math.sqrt(math.sin(magnitude)**2+math.cos(magnitude-1)**2)
        elif projectionMode==3: #Stereographic (the best projection)
            if sR>0:
                shragnitude=math.asin(sR/math.sqrt(smagnitude**2+v[2]**2))
                rotaterinos=[]
                for i in range(2):
                    rotagnitude=rotate2D(smagnitude+[v[2]],shragnitude*(1-2*i))
                    guacnitude=projectSpaceToScreen([rotagnitude[0],0,rotagnitude[1]],0) #frankly delicious
                    rotaterinos.append(math.atan2(math.sqrt(sum([guacnitude[j]**2 for j in range(2)]),v[2])))
                newRadius=rotaterinos[1]-rotaterinos[0]
                magnitude=sum(rotaterinos)/2
            else:
                magnitude=math.sin(magnitude)/1-math.cos(magnitude)
        direction=math.atan2(v[0],v[1])
        outputPosition=[magnitude*math.cos(direction+math.pi*i) for i in 2]
        if not(newRadius==0):
            outputPosition.append(newRadius)
        return outputPosition

def rotateVector(v,q,perspective,*sR): #sR is stereographic radius (to be passed through to perspective function)
    rotated=quaternionMultiply(quaternionMultiply(q,[0]+v),quaternionConjugate(q))
    if perspective==1:
        return projectSpaceToScreen([rotated[i]-cameraPosition[i] for i in range[dims]],sR)
    else:
        return rotated

def screenPosition(position,*sR):
    return rotateVector(position,cameraOrientation,perspectiveMode,sR)

def render3D():
    screenPositions=[screenPosition([squares[i][di][0]-cameraPosition[di] for di in range(dims)],squares[i][1][0]) for i in range(len(squares))] #is 4 elements long instead of 3 if stereographic (last element is the screen radius (do not forget (very important)))
    distances=[sum([screenPositions[i][di]**2 for di in range(dims)]) for i in range(len(squares))] #is actually distances squared (to be more elegant)
    powers=[distances[i]-squares[i][1][0]**2 for i in range(len(squares))] #render order is by spheres' "powers" (squared distance from centre to camera minus squared radius)
    for i in sorted(zip([i for i in range(len(squares))], powers)): #probably not most elegant solution, from the answer to sorting lists by other lists here: https://stackoverflow.com/a/6618543/
        if projectionMode==4:
            sizes=[screenPositions[i][3]]*(dims-1) #delightfully devilish
        else:
            sizes=squares[i][1]
            if perspectiveMode==1:
                if sizes!=1:
                    sizes=math.asin(sizes[0]/math.sqrt(distances[i]+squares[i][1][0]**2))*2*max(size)*(dims-1)
                else:
                    sizes=math.atan(sizes[0]/math.sqrt(distances[i]))*2*max(size)*(dims-1) #you would think is wrong, but is actually identical at positive distance (which is always), atan(r/x)-asin(r/sqrt(r^2+x^2))=0 when x is positive (otherwise it is a corkscrew shape dependent on the angle from x to r)
        drawShape(sizes[0],sizes[1],screenPositions[0],screenPositions[1],i[3],1)

def lineCollision(m1,v1,m2,v2):
    return [((m1-m2)*v1+(2*m2)*v2)/(m1+m2),((m2-m1)*v2+(2*m1)*v1)/(m1+m2)]

def tangentSphereCollision(spheres,refract,n): #n is refractive index
    dM=0
    differences=[[]]*2
    sphereVs=[[]]*2
    for di in range(dims):
        for i in range(2):
            differences[i].append(spheres[1][0][di][i]-spheres[0][0][di][i])
        dM+=differences[0][di]**2
    dM=math.sqrt(dM)
    if spheres[1][2]==0:
        #will be for raytracing
        Ca=2*dotProduct(differences[1],differences[0])/(dM**2)
        collisionDeltaV=[Ca*differences[0][di] for di in range(dims)]
        discriminant=1-((n**2)*(1-Ca**2))
        return [spheres[1][0][di][1]+n*(differences[0][di]-2*collisionDeltaV[di])-(differences[1][di]*math.sqrt(discriminant)) if (refract==1 and discriminant>0) else spheres[1][0][i][1]+collisionDeltaV[i]-2*spheres[0][0][i][1] for di in range(dims)]
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
            gravity=gravitationalConstant/math.sqrt(sum([di**2 for di in differences])**3)
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
                if 0<=t<=timeToProceed:
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

gain=1
angularVelocityConversionFactor=1/FPS/4
fieldOfView=math.pi
run=True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    physics()
    screen.fill(black)
    keys=pygame.key.get_pressed()
    arrowAccs=[(keys[pygame.K_RIGHT]-keys[pygame.K_LEFT]),(keys[pygame.K_DOWN]-keys[pygame.K_UP])]
    if arrowAccs[0]!=0!=arrowAccs[1]: #Will normalise such that absolute value of 6D vector of spatial and angular acceleration is 1 but there are only 2 currently
        arrowAccs=[arrowAccs[i]/math.sqrt(2) for i in range(2)]
    if dims==3:
        for di in range(1,4): #Quaternions are pretty cool I believe
            cameraOrientation[1][di]+=arrowAccs[di]*gain*angularVelocityConversionFactor
            cameraOrientation[1][di]/=1+drag #cameraOrientation[1][0] isn't used (because they're yaw,pitch,roll (but they pretend to be i,j,k))
        mouse=pygame.mouse
        mouserino=mouse.get_rel*mouse.get_pressed
        mouserino.append(0)
        cameraOrientation[0]=rotateByLocalGimbals(cameraOrientation[0],[cameraOrientation[1][di+1]+mouserino[di]*fieldOfView/size[0] for di in range(3)])
        render3D()
    else:
        if dims==2:
            for di in range(2):
                squares[0][0][di][1]+=arrowAccs[di]*gain
        for i in range(len(squares)):
            drawShape(squares[i][1][0]+20,squares[i][1][1]+20,squares[i][0][0][0]-20,squares[i][0][1][0]-20,squares[i][3],1)
    pygame.display.flip()
    clock.tick(FPS)
