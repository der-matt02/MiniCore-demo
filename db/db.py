from db.db_connection import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Date


class Empleado(Base):
    __tablename__ = "empleados"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    apellido = Column(String)


class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)


class Tarea(Base):
    __tablename__ = "tareas"

    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String)
    fecha_inicio = Column(Date)
    estimado = Column(Integer)
    estado = Column(String)
    id_empleado = Column(Integer, ForeignKey("empleados.id"))
    id_proyecto = Column(Integer, ForeignKey("proyectos.id"))
