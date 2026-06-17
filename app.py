
# asignacion de las colecciones a variables
invitados = db["invitados"]
eventos = db["eventos"]
# ciclo infinito para mantener el menu activo
while True:
    print("\nIntegrantes:")
    print("Benjamin Fajardo, Maximiliano Fajardo")
    print("==============================================")
    print("        sistema de eventos         ")
    print("==============================================")
    print("1. requerimiento 1: listar eventos (filtros)")
    print("2. requerimiento 2: filtrar invitados")
    print("3. requerimiento 3: validar acceso ($lookup)")
    print("4. requerimiento 4: top 3 eventos confirmados")
    print("5. salir")
    print("==============================================")
    
    opc = input("seleccione una opcion: ").strip()
    
    try:
        # requerimiento 1: listar eventos mostrando campos especificos
        if opc == "1":
            print("\n=== listado de eventos ===")
            cat = input("filtrar por categoria (charla/workshop/meetup) o [enter] para todos: ").strip().lower()
            
            # operador ternario para crear un filtro vacio o por categoria
            filtro = {"categoria": cat} if cat else {}
            # proyeccion para incluir solo campos requeridos y ocultar el _id
            proyeccion = {"codigo": 1, "nombre": 1, "fecha": 1, "lugar": 1, "categoria": 1, "_id": 0}
            
            # metodo find para consultar documentos con filtros y proyecciones
            result = eventos.find(filtro, proyeccion)
            
            # ciclo for para recorrer los resultados del cursor de mongodb
            for e in result:
                print(f"codigo: {e['codigo']} | nombre: {e['nombre']} | fecha: {e['fecha']} | lugar: {e['lugar']} | categoria: {e['categoria']}")

        # requerimiento 2: filtrar invitados usando expresiones regulares
        elif opc == "2":
            print("\n=== filtrar invitados por patron ===")
            print("a) buscar por nombre parcial (case-insensitive)")
            print("b) buscar por dominio de correo (ej: @empresa.cl)")
            sub_opc = input("seleccione subtipo (a/b): ").strip().lower()
            
            if sub_opc == "a":
                txt = input("ingrese nombre o parte de el: ").strip()
                # re.compile con re.IGNORECASE busca texto ignorando mayusculas y minusculas
                filtro = {"nombre": re.compile(txt, re.IGNORECASE)}
            elif sub_opc == "b":
                dom = input("ingrese el dominio de correo: ").strip()
                # re.escape limpia caracteres especiales y el simbolo $ busca texto al final
                patron_correo = re.escape(dom) + "$"
                filtro = {"correo": re.compile(patron_correo, re.IGNORECASE)}
            else:
                print("opcion invalida.")
                continue
                
            result = invitados.find(filtro, {"_id": 0})
            for i in result:
                print(f"rut: {i['rut']} | nombre: {i['nombre']} | correo: {i['correo']} | estado: {i['estado']}")

        # requerimiento 3: validacion cruzada de accesos con $lookup
        elif opc == "3":
            print("\n=== validacion de acceso cruzado ===")
            cod = input("codigo del evento (ej: evt-2025-001): ").strip().upper()
            rut = input("rut del invitado (ej: 11.009.876-3): ").strip()
            
            # lista pipeline de agregacion para procesar datos por etapas
            union = [
                # $match filtra el documento del evento especifico
                {"$match": {"codigo": cod}},
                # $unwind desarma el array de invitados convirtiendo cada elemento en un documento
                {"$unwind": "$invitados"},
                # $match filtra el subdocumento que coincida con el rut ingresado
                {"$match": {"invitados.rut": rut}},
                {
                    # $lookup une la coleccion actual con invitados usando el campo rut
                    "$lookup": {
                        "from": "invitados",
                        "localField": "invitados.rut",
                        "foreignField": "rut",
                        "as": "perfil_global"
                    }
                },
                # $unwind aplana el array resultante del lookup para leerlo directo
                {"$unwind": "$perfil_global"}
            ]
            
            # metodo aggregate ejecuta las etapas de la lista pipeline anterior
            result = list(eventos.aggregate(union))
            
            if not result:
                print("\n[denegado]: el invitado no pertenece a este evento o el evento no existe.")
            else:
                data = result[0]
                # extraccion de estados desde subdocumento y coleccion externa cruzada
                est_evento = data["invitados"]["estado"]
                est_global = data["perfil_global"]["estado"]
                
                print(f"\ninvitado: {data['perfil_global']['nombre']}")
                print(f"estado en evento: {est_evento.upper()} | estado maestro: {est_global.upper()}")
                
                # logica condicional para validar los permisos de acceso cruzados
                if est_global == "bloqueado":
                    print("[resultado]: denegado. usuario bloqueado globalmente.")
                elif est_evento == "confirmado":
                    print("[resultado]: permitido. acceso autorizado.")
                else:
                    print(f"[resultado]: denegado. su estado es '{est_evento}'.")

        # requerimiento 4: estadisticas agregadas - top 3 eventos
        elif opc == "4":
            print("\n=== top 3 eventos con mas confirmados ===")
            # pipeline estadistico para contar y ordenar datos estructurados
            estadistica = [
                {"$unwind": "$invitados"},
                {"$match": {"invitados.estado": "confirmado"}},
                # $group agrupa los documentos por nombre y $sum calcula el total de cada grupo
                {"$group": {"_id": "$nombre", "total": {"$sum": 1}}},
                # $sort ordena los grupos de mayor a menor usando el valor -1
                {"$sort": {"total": -1}},
                # $limit restringe la salida para mostrar solo los 3 primeros documentos
                {"$limit": 3}
            ]
            
            result = eventos.aggregate(estadistica)
            pos = 1
            for r in result:
                print(f"{pos}°. {r['_id']} - confirmados: {r['total']}")
                pos += 1

        # opcion para detener la ejecucion del menu interactivo
        elif opc == "5":
            print("saliendo del sistema...")
            break
        else:
            print("opcion incorrecta.")
            
    except Exception as error:
        # captura general de errores para evitar que la aplicacion se caiga o colapse
        print(f"ocurrio un error en el sistema: {error}")
