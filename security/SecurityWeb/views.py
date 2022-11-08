# Create your views here.
from ast import For
from email.policy import strict
from http import client
from pydoc import describe
from re import U, template
from sqlite3 import Date
import string
from tkinter import EXCEPTION
from traceback import print_tb
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
# adjuntamos la libreria de autenticar 
from django.contrib.auth import authenticate,logout,login as login_autent
#agregar decorador para impedir el ingreso a las paginas sin estar registrado
from django.contrib.auth.decorators import login_required, permission_required
from django.db import connection
from .models import Actividad, CheckList, Cliente, Room, Message, Profesional

from django.http import HttpResponse, JsonResponse

import cx_Oracle #para ocupar varibles de oracle
import requests #llamados de api C#
import json

from datetime import date, datetime # libreria para saber la fecha actual

# Create your views here.

def index(request):
    return render(request,'index.html')

def contacto(request):
    return render(request,'contacto.html')

def visionMision(request):
    return render(request,'vision-mision.html')

def plan(request):
    return render(request,'plan.html')

def login(request):
    data = {
        'rubro':listar_rubro()
    }
    if 'registro' in request.POST:
        rutCliente = request.POST.get('rut')
        razonSocial = request.POST.get('razonSocial')
        numeroContacto = request.POST.get('numeroContacto')
        rubro = request.POST.get('rubro')
        correo = request.POST.get('correo')
        contrasena = request.POST.get('pass')
        try:
            u = User.objects.get(username=razonSocial)
            data['mensaje'] = 'Usuario ya ingresado'
            u = User.objects.get(email=correo)
            data['mensaje'] = 'Correo ya ingresado'
            return render(request,'login.html',data)
        except:
            u = User()
            u.username = razonSocial
            u.email = correo
            u.set_password(contrasena)
            salida = agregar_usuario(rutCliente, razonSocial, numeroContacto, rubro,  correo, u.password)
            u.save()
        if salida == 1:
            data['mensaje'] = 'Se registro correctamente.'
        else:
            data['mensaje'] = 'Error en el registro vuelva intentar.'
        return render(request,'login.html',data)

    elif 'login' in request.POST:
        user = request.POST.get("user")
        password = request.POST.get("pass")
        us = authenticate(request,username=user,password=password)
        if us is not None and us.is_active:
            login_autent(request,us)
            return render(request,'index.html',{'user':us})
        else:
            return render(request,'login.html',{'msg':'Usuario o contraseña incorrecta'})

    return render(request,'login.html',data)

def loginProfesional(request):
    data = {}

    if 'registro' in request.POST:
        rutProfesional = request.POST.get('rut')
        primerNombre = request.POST.get('primerNombre')
        segundoNombre = request.POST.get('segundoNombre')
        primerApelido = request.POST.get('primerApelido')
        segundoApelido = request.POST.get('segundoApelido')
        numeroContacto = request.POST.get('numeroContacto')
        correo = request.POST.get('correo')
        contrasena = request.POST.get('pass')
        name = primerNombre[:4]+primerApelido[:3]
        print(name)

        try:
            u = User.objects.get(username=name)
            data['mensaje'] = 'Usuario ya ingresado'
            u = User.objects.get(email=correo)
            data['mensaje'] = 'Correo ya ingresado'
            return render(request,'loginProfesional.html',data)
        except:
            u = User()
            u.username = name
            u.email = correo
            u.set_password(contrasena)
            profesional = Profesional(
                rutprofesional = rutProfesional,
                primernombre = primerNombre,
                segundonombre = segundoNombre,
                primerapellido = primerApelido,
                segundoapellido = segundoApelido,
                numerocontacto = numeroContacto,
                isvigente = "1",
            )
            profesional.save()
            salida = agregar_usuario_profesional(rutProfesional,correo, u.password)
            u.save()
            if salida == 1:
                data['mensaje'] = 'Se registro correctamente.'
            else:
                data['mensaje'] = 'Error en el registro vuelva intentar.'
                return render(request,'loginProfesional.html',data)
        return render(request,'loginProfesional.html',data)

    elif 'login' in request.POST:
        user = request.POST.get("user")
        password = request.POST.get("pass")
        us = authenticate(request,username=user,password=password)
        if us is not None and us.is_active:
            login_autent(request,us)
            return render(request,'index.html',{'user':us})
        else:
            return render(request,'loginProfesional.html',{'msg':'Usuario o contraseña incorrecta'})

    return render(request,'loginProfesional.html',data)

def logout_vista(request):
    logout(request)
    return render(request,'login.html')

@login_required(login_url='/login/')
def contratar(request):
    user = request.user.get_username()
    dataMsg = {}
    if request.method == 'POST':
        url = "https://localhost:7000/ComprobantePago/SaveComprobante"

        numeroTarjeta = request.POST.get('numeroTarjeta')
        nombreTitular = request.POST.get('nombreTitular')
        mes = request.POST.get('mes')
        anio = request.POST.get('anio')
        fechaValida = mes+anio
        cvv = request.POST.get('cvv')
        monto = 60
        tipoMoneda = "CH"
        canalPago = 1
        descripcion = "Contratacion de Plan"

        headers = {'Content-Type': 'application/json'}

        payload = json.dumps({
            'numeroTarjeta':numeroTarjeta,
            'nombreTitular':nombreTitular,
            'fechaValida':fechaValida,
            'monto':monto,
            'tipoMoneda':tipoMoneda,
            'cvv':cvv
        })
        
        response = requests.request("POST", url, headers=headers, data=payload, verify=False )

        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))

            idcomprobante = data['idcomprobante']
            montoPago = data['montoPago']
            message = data['message']
            fechaRegistro = data['fechaRegistro']
            # Format la fecha para el ingreso a base de datos
            fechaRegistro = fechaRegistro.replace("T","")
            fechaRegistro = fechaRegistro[:-14]
      
            salida = SP_CONTRATO_PAGO(user,fechaRegistro,montoPago,canalPago,idcomprobante,descripcion)
            if salida == 1:
                dataMsg['mensaje'] = message
            else:
                dataMsg['mensaje'] = 'Error al contratar el plan'

    return render(request,'plan.html',dataMsg)

@login_required(login_url='/login/')
def asesoria(request):
    data = {
        'tipo_actividad':listar_tipo_actividad()
    }
    user = request.user.get_username()
    if request.method == 'POST':
        idTipoAsesoria = request.POST.get('tip_asesoria')
        descripcion = request.POST.get('descripcion')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_termino = request.POST.get('fecha_termino')
        hora_inicio = request.POST.get('hora_inicio')
        if hora_inicio is not None:
            hora_inicio = fecha_inicio+' '+hora_inicio
        hora_termino = request.POST.get('hora_termino')
        if hora_termino is not None:
            hora_termino = fecha_termino+' '+hora_termino
        cant_asistentes = request.POST.get('cant_asistentes')
        direccion = request.POST.get('direccion')
        fecha_registro = datetime.now()
        fecha_format = fecha_registro.strftime("%m%d%Y%H%M%S")
        room = user +" "+ fecha_format
        print(idTipoAsesoria)
 
        if idTipoAsesoria == "4":
            new_room = Room(
            sala = room
            )
            new_room.save()
            data['sala'] = "Se creo tu sala con exito : " + room

        salida = SP_INGRESAR_SOLICITUD(descripcion,fecha_inicio,fecha_termino,hora_inicio,hora_termino,cant_asistentes,fecha_registro,direccion,user,idTipoAsesoria)
        if salida == 1:
            data['mensaje'] = 'Solicitud Ingresada'
        else:
            data['mensaje'] = 'Error al ingresar solicitud'

    return render(request,'asesoria.html',data)

@login_required(login_url='/login/')
def perfil(request):
    user = request.user.get_username()
    data = {'solicitud':listar_usuario(user),
            'count':count_asesoria_cliente(user)
    }
    if request.method == 'POST':
        correo = request.POST.get('email')
        telefono = request.POST.get('telefono')
        password = request.POST.get('password')
        password_confirmed= request.POST.get('password_confirmed')

        if password != None:
            if password == password_confirmed:
                u = User.objects.get(username__exact=user)
                u.email = correo
                u.set_password(password)
                u.save()
                salida = SP_MODIFICAR_USER_PASS(telefono, correo, user, u.password)
                if salida == 1:
                    data['mensaje'] = 'Modificado correctamente'
                else:
                    data['mensaje'] = 'No se ha podido modificar'
            else:
                data['mensaje'] = 'Las contraseñas deben ser iguales'
        else:
            salida = SP_MODIFICAR_USER(telefono, correo, user)
             
            if salida == 1:
                data['mensaje'] = 'Modificado correctamente'
            else:
                data['mensaje'] = 'No se ha podido modificar'
    return render(request,'perfil.html',data)

@login_required(login_url='/login/')
def asesoriaCliente(request):
    user = request.user.get_username()
    data = {
        'solicitud':listar_usuario(user),
        'asesoria':listar_asesoria_cliente(user),
        'count':count_asesoria_cliente(user)
    }
    return render(request,'asesoria_cliente.html',data)

@login_required(login_url='/login/')
def contratoCliente(request):
    user = request.user.get_username()
    data = {
        'solicitud':listar_usuario(user),
        'contrato':listar_contrato_cliente(user),
        'count':count_contrato_cliente(user)
    }
    return render(request,'contrato_cliente.html',data)

@permission_required('SecurityWeb.add_check',login_url='/login/')
@login_required(login_url='/login/')
def checklist(request):
    user = request.user.get_username()
    data = {
        'solicitud':listar_usuario(user)
    }

    if request.POST:
        usuarioCliente = request.POST.get("UsuarioCliente")
        isSeniales = request.POST.get("isSeniales")
        isElemento = request.POST.get("isElemento")
        isMaterial = request.POST.get("isMaterial")
        isRedHidrica = request.POST.get("isRedHidrica")
        isIluminaria = request.POST.get("isIluminaria")
        isSeguroEmp = request.POST.get("isSeguroEmp")
        isPlanSeg = request.POST.get("isPlanSeg")
        descripcion = request.POST.get("descripcion")
        fecha_registro = datetime.now()

        salida = SP_INGRESAR_CHECKLIST(usuarioCliente,isSeniales,isElemento,isMaterial,isRedHidrica,isIluminaria,isSeguroEmp,isPlanSeg,descripcion,fecha_registro)
        if salida == 1:
            data['mensaje'] = 'Check List Ingresado Correctamente.'
        else:
            data['mensaje'] = 'Error al Check List'
        
    return render(request,'check-list.html',data)

@permission_required('SecurityWeb.add_check',login_url='/login/')
@login_required(login_url='/login/')
def check_list_index(request):
    checklist = CheckList.objects.all().order_by('idcheck')
    data = {
        'checklist':checklist
    }
    try:
        if request.POST:
            id = request.POST.get("id")
            checklist = CheckList.objects.filter(idcheck=id).order_by('idcheck')
            data['checklist'] = checklist
            return render(request,'check-list-index.html',data)
    except:
        checklist = CheckList.objects.all().order_by('idcheck')
        data['checklist'] = checklist
        return render(request,'check-list-index.html',data)
    return render(request,'check-list-index.html',data)

@permission_required('SecurityWeb.mod_check',login_url='/login/')
@login_required(login_url='/login/')
def check_list_modificar(request,idcheck = None):
    try:

        check = CheckList.objects.filter(idcheck=idcheck)
        actividad = Actividad.objects.get(idcheck = idcheck)
        rutCliente = actividad.rutcliente
        cliente = Cliente.objects.get(rutcliente = rutCliente.rutcliente)

        data = {
            'checklist':check,
            'Razonsocial':cliente.razonsocial
        }

        if request.POST:
            isSeniales = request.POST.get("isSeniales")
            isElemento = request.POST.get("isElemento")
            isMaterial = request.POST.get("isMaterial")
            isRedHidrica = request.POST.get("isRedHidrica")
            isIluminaria = request.POST.get("isIluminaria")
            isSeguroEmp = request.POST.get("isSeguroEmp")
            isPlanSeg = request.POST.get("isPlanSeg")
            descripcion = request.POST.get("descripcion")
            fecha_registro = datetime.now()
            
            try:
                check = CheckList.objects.get(idcheck=idcheck)
                check.isseniales = isSeniales
                check.iselementoseguridad = isElemento
                check.ismaterial = isMaterial
                check.isredagua = isRedHidrica
                check.isluminaria = isIluminaria
                check.isseguro = isSeguroEmp
                check.istrabajoseguro = isPlanSeg
                check.fecharegistro = fecha_registro
                check.descripcion = descripcion
                check.save()
                data['mensaje'] = 'Check List Modificado'

            except:
                data['mensaje'] = 'Error al Modificar Check List'

        return render(request,'check-list-modificar.html',data)
    except:
        return render(request,'Error/error.html',{'error':'Error 405 Data not Found.', 'id': 'El ID Check List No existe : '+str(idcheck)})

@login_required(login_url='/login/')
def listaChat(request):
    room = Room.objects.all()
    return render(request, 'chat/chat-index.html')

@login_required(login_url='/login/')
def home(request):
    return render(request, 'chat/home.html')

@login_required(login_url='/login/')
def room(request, room):
    username = request.GET.get('username')
    room_details = Room.objects.get(sala=room)
    return render(request, 'chat/room.html', {
        'username': username,
        'room': room,
        'room_details': room_details.sala
    })

@login_required(login_url='/login/')
def checkview(request):
    room = request.POST['room_name']
    username = request.POST['username']

    if Room.objects.filter(sala=room).exists():
        return redirect('sala/'+room+'/?username='+username)
    else:
        new_room = Room(
            sala = room
        )
        new_room.save()
        return redirect('sala/'+room+'/?username='+username)

@login_required(login_url='/login/')
def send(request):
    if request.POST:
        message = request.POST.get('message')
        username = request.POST.get('username')
        room_id = request.POST.get('room_id')
        registro = datetime.now()

        new_message = Message(
            valor=message, 
            username=username, 
            room=room_id,
            datetime= registro
        )
        new_message.save()
        return HttpResponse('Message sent successfully')

@login_required(login_url='/login/')
def getMessages(request, room):
    room_details = Room.objects.get(sala=room)
    messages = Message.objects.filter(room=room_details.sala).order_by('idmessage')

    return JsonResponse({"messages":list(messages.values())})

#----------------- Listado -----------------
def agregar_usuario(rutCliente, razonSocial, numeroContacto,rubro,correo,contrasena):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor()
    salida = cursor.var(cx_Oracle.NUMBER)
    cursor.callproc("SP_AGREGAR_USUARIO_CLIENTE",[rutCliente, razonSocial, numeroContacto, rubro, correo,  contrasena, salida])
    return salida.getvalue()

def agregar_usuario_profesional(rutProfesional, correo, contrasenia):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor()
    salida = cursor.var(cx_Oracle.NUMBER)
    cursor.callproc("SP_AGREGAR_USUARIO_PROFESIONAL",[rutProfesional, correo, contrasenia, salida])
    return salida.getvalue()

def SP_MODIFICAR_USER_PASS(numeroContacto, correo, razonSocial, contrasena):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor()
    salida = cursor.var(cx_Oracle.NUMBER)
    cursor.callproc("SP_MODIFICAR_USER_PASS",[numeroContacto, correo, razonSocial , contrasena, salida])
    return salida.getvalue()

def SP_MODIFICAR_USER(numeroContacto, correo, razonSocial):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor()
    salida = cursor.var(cx_Oracle.NUMBER)
    cursor.callproc("SP_MODIFICAR_USER",[numeroContacto, correo, razonSocial, salida])
    return salida.getvalue()

def SP_CONTRATO_PAGO(razonSocial, fechaRegistro, montoPago, idCanalPago, idComprobantePago, descripcion):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor()
    salida = cursor.var(cx_Oracle.NUMBER)
    cursor.callproc("SP_PAGO_CONTRATO",[razonSocial, fechaRegistro, montoPago, idCanalPago, idComprobantePago, descripcion, salida])
    return salida.getvalue()

def SP_INGRESAR_SOLICITUD(descripcion, fecha_inicio, fecha_termino, hora_inicio, hora_termino, cantAsistente, fecha_registro, direccion, razonSocial, idTipo):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor()
    salida = cursor.var(cx_Oracle.NUMBER)
    cursor.callproc("SP_INGRESAR_SOLICITUD",[descripcion, fecha_inicio, fecha_termino, hora_inicio, hora_termino, cantAsistente, fecha_registro, direccion, razonSocial, idTipo, salida])
    return salida.getvalue()

def SP_INGRESAR_CHECKLIST(razonSocial,isSeniales,isElemento,isMaterial,isRedHidrica,isIluminaria,isSeguroEmp,isPlanSeg,descripcion,fecha_registro):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor()
    salida = cursor.var(cx_Oracle.NUMBER)
    cursor.callproc("SP_INGRESAR_CHECKLIST",[razonSocial,isSeniales,isElemento,isMaterial,isRedHidrica,isIluminaria,isSeguroEmp,isPlanSeg,descripcion,fecha_registro,salida])
    return salida.getvalue()


def listar_asesoria_cliente(user):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor() #llama 
    out_cur = django_cursor.connection.cursor() #recibe
    cursor.callproc("SP_ASESORIACLIENTE",[user,out_cur])

    lista = []
    for fila in out_cur:
        lista.append(fila)
    return lista

def count_asesoria_cliente(user):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor() #llama 
    out_cur = django_cursor.connection.cursor() #recibe
    cursor.callproc("SP_COUNT_ASESORIA",[user,out_cur])

    lista = []
    for fila in out_cur:
        lista.append(fila)
    return lista

def listar_contrato_cliente(user):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor() #llama 
    out_cur = django_cursor.connection.cursor() #recibe
    cursor.callproc("SP_CONTRATOCLIENTE",[user,out_cur])

    lista = []
    for fila in out_cur:
        lista.append(fila)
    return lista

def count_contrato_cliente(user):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor() #llama 
    out_cur = django_cursor.connection.cursor() #recibe
    cursor.callproc("SP_COUNT_CONTRATO",[user,out_cur])

    lista = []
    for fila in out_cur:
        lista.append(fila)
    return lista

def listar_rubro():
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor() #llama 
    out_cur = django_cursor.connection.cursor() #recibe
    cursor.callproc("SP_RUBRO",[out_cur])

    lista = []
    for fila in out_cur:
        lista.append(fila)
    return lista

def listar_tipo_actividad():
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor() #llama 
    out_cur = django_cursor.connection.cursor() #recibe
    cursor.callproc("SP_TIPO_ACTIVIDAD",[out_cur])

    lista = []
    for fila in out_cur:
        lista.append(fila)
    return lista

def listar_usuario(user):
    django_cursor = connection.cursor()
    cursor = django_cursor.connection.cursor() #llama 
    out_cur = django_cursor.connection.cursor() #recibe
    cursor.callproc("SP_USUARIO",[user,out_cur])
    
    lista = []
    for fila in out_cur:
        lista.append(fila)
    return lista      