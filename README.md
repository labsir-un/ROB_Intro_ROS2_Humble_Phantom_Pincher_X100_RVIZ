
<div align="center">
<picture>
    <source srcset="https://imgur.com/5bYAzsb.png" media="(prefers-color-scheme: dark)">
    <source srcset="https://imgur.com/Os03JoE.png" media="(prefers-color-scheme: light)">
    <img src="https://imgur.com/Os03JoE.png" alt="Escudo UNAL" width="350px">
</picture>

<h3>Curso de Robótica 2025-II</h3>

<h1>PhantomX Pincher X100 en ROS 2 Humble</h1>

<h2>Guía 05 - Control del Robot Real y Visualización en RViz</h2>

<h4>Pedro Fabián Cárdenas Herrera<br>
    Manuel Felipe Carranza Montenegro</h4>
</div>

<div align="justify">

## 1. Introducción

En la **Guía 04** se creó un paquete de control en Python para mover los servomotores del PhantomX Pincher X100 usando ROS 2 Humble y la librería `dynamixel_sdk`.

En esta guía extendemos ese trabajo para:

- **Visualizar el robot en 3D en RViz** usando un modelo `xacro/URDF`.
- **Sincronizar RViz con el robot real** publicando el estado de las articulaciones en el tópico `/joint_states`.
- **Integrar todo en una sola interfaz gráfica (Tkinter)**, que permite:
  - Mover las articulaciones mediante sliders y campos numéricos.
  - Lanzar y cerrar RViz desde un botón, sin abrir otra terminal.
  - Ver en RViz el movimiento del robot en tiempo real.

El resultado final es un sistema donde el PhantomX se mueve físicamente y se visualiza simultáneamente en RViz.

---

## 2. Objetivos

1. Crear un **paquete de descripción** `pincher_description` con:
   - Archivos de malla (`.stl`) del robot.
   - Un archivo `robot.xacro` con la kinemática del Pincher.
   - Un `display.launch.py` que cargue el modelo y abra RViz.

2. Modificar el paquete de control `pincher_control` para:
   - Publicar correctamente en `/joint_states`.
   - Mapear los valores Dynamixel a radianes corrigiendo el signo de las articulaciones.
   - Incluir un botón que ejecute `ros2 launch pincher_description display.launch.py`.

---

## 3. Prerrequisitos

Antes de comenzar debes tener:

- **Ubuntu 22.04 LTS** correctamente instalado (nativo, VM o WSL2 con soporte gráfico).
- **ROS 2 Humble** instalado y funcionando.
- Workspace creado, compilado y “sourceado”:

  ```bash
  mkdir -p ~/ros_humble/phantom_ws/src
  cd ~/ros_humble/phantom_ws
  colcon build
  source /opt/ros/humble/setup.bash
  source install/setup.bash
  ```

- PhantomX Pincher X100 conectado vía USB2Dynamixel en `/dev/ttyUSB0` y servomotores configurados con IDs `[1, 2, 3, 4, 5]` (o los que uses).

---

## 4. Estructura general del repositorio

El nuevo repositorio está pensado para vivir dentro del workspace `phantom_ws`:

```bash
phantom_ws/
├── src/
│   ├── pincher_control/      # Paquete de control (Python + GUI + /joint_states)
│   └── pincher_description/  # Paquete de descripción (xacro + meshes + launch)
└── ...
```

Dentro de cada paquete tenemos, de forma simplificada:

```bash
pincher_description/
├── package.xml
├── CMakeLists.txt (o setup.py si usas ament_python)
├── urdf/
│   └── robot.xacro
├── meshes/
│   ├── px100_1_base.stl
│   ├── px100_2_shoulder.stl
│   ├── px100_3_upper_arm.stl
│   ├── px100_4_forearm.stl
│   ├── px100_5_gripper.stl
│   ├── px100_6_gripper_prop.stl
│   ├── px100_7_gripper_bar.stl
│   └── px100_8_gripper_finger.stl
└── launch/
    └── display.launch.py
```

```bash
pincher_control/
├── package.xml
├── setup.py
└── pincher_control/
    ├── __init__.py
    └── control_servo.py   # Nodo ROS 2 + GUI + publicador /joint_states
```

---

## 5. Uso rápido del sistema completo

### 5.1 Compilar y cargar entorno

Desde la raíz del workspace:

```bash
cd ~/ros_humble/phantom_ws
colcon build
source /opt/ros/humble/setup.bash
source install/setup.bash
```

> **Tip:** añade `source ~/ros_humble/phantom_ws/install/setup.bash` a tu `~/.bashrc` para no repetirlo.

### 5.2 Ejecutar el nodo de control con GUI

```bash
ros2 run pincher_control control_servo
```

Se abrirá la ventana de Tkinter con:

- **Pestaña 1:** Sliders en tiempo real para cada motor.
- **Pestaña 2:** Entrada de valores en bits (0–4095) por motor.
- **Pestaña 3:** Información de RViz y botón para lanzar/cerrar.

### 5.3 Lanzar RViz desde el botón

En la pestaña **“Visualización RViz”**:

1. Pulsa el botón **“LANZAR RViz”**.
2. El nodo ejecutará internamente:

   ```bash
   ros2 launch pincher_description display.launch.py
   ```

3. Se abrirá RViz con:
   - El modelo 3D del Pincher.
   - `robot_state_publisher` usando el `robot.xacro`.
   - `RobotModel` configurado para leer de `/robot_description`.

Mientras la GUI esté publicando en `/joint_states`, el robot de RViz se moverá de forma sincronizada con el robot físico.

4. Para cerrar, usa el botón **“DETENER RViz”** dentro de la misma GUI.

---

## 6. Paso a paso: de cero a RViz

### 6.1 Paquete de control `pincher_control` (resumen)

Este paquete hereda lo desarrollado en la guía anterior: un nodo que inicializa los Dynamixel usando `dynamixel_sdk`, configura torque, velocidad y mueve los motores.

En esta nueva versión se añaden:

1. **Publicador de `JointState`:**

   ```python
   from sensor_msgs.msg import JointState

   self.joint_state_pub = self.create_publisher(JointState, '/joint_states', 10)
   self.current_joint_positions = [0.0] * 5  # waist, shoulder, elbow, wrist, gripper
   self.joint_names = ['waist', 'shoulder', 'elbow', 'wrist', 'gripper']
   ```

2. **Función para convertir de pasos Dynamixel a radianes:**

   ```python
   def dxl_to_radians(self, dxl_value):
       # 0–4095 → -150° a +150° ≈ -2.618 a +2.618 rad
       return (dxl_value - 2048) * (2.618 / 2048.0)
   ```

   Para las articulaciones que giran al revés en RViz (2, 3 y 4), se puede aplicar simplemente un signo:

   ```python
   SIGN = [+1, -1, -1, -1, +1]  # ej. waist, shoulder, elbow, wrist, gripper
   self.current_joint_positions[i] = SIGN[i] * self.dxl_to_radians(goal)
   ```

3. **Publicación periódica en `/joint_states`:**

   ```python
   def publish_joint_states(self):
       joint_state = JointState()
       joint_state.header.stamp = self.get_clock().now().to_msg()
       joint_state.name = self.joint_names
       joint_state.position = self.current_joint_positions
       self.joint_state_pub.publish(joint_state)

   self.create_timer(0.1, self.publish_joint_states)  # 10 Hz
   ```

4. **Actualización de `current_joint_positions` cada vez que mueves un motor:**

   ```python
   def move_motor(self, motor_id, position):
       # ... escribir posición en el motor ...
       joint_index = self.dxl_ids.index(motor_id)
       self.current_joint_positions[joint_index] = \
           SIGN[joint_index] * self.dxl_to_radians(position)
   ```

5. **Ejecución concurrente de ROS 2 y Tkinter**

Para que el nodo pueda publicar en ROS 2 mientras la GUI corre, se usa un hilo separado:

```python
def main(args=None):
    rclpy.init(args=args)

    controller = PincherController()

    spin_thread = threading.Thread(
        target=rclpy.spin,
        args=(controller,),
        daemon=True
    )
    spin_thread.start()

    try:
        gui = PincherGUI(controller)
        gui.run()
    finally:
        controller.close()
        controller.destroy_node()
        rclpy.shutdown()
```

---

### 6.2 Paquete de descripción `pincher_description`

#### 6.2.1 Crear el paquete

Desde `phantom_ws/src`:

```bash
cd ~/ros_humble/phantom_ws/src
ros2 pkg create --build-type ament_cmake pincher_description
```

(Se puede usar también `ament_python` si prefieres.)

#### 6.2.2 Añadir `meshes`, `urdf` y `rviz`

Dentro de `pincher_description` crea las carpetas:

```bash
mkdir -p pincher_description/meshes
mkdir -p pincher_description/urdf
mkdir -p pincher_description/rviz
mkdir -p pincher_description/launch
```

Copia los archivos `.stl` del PhantomX Pincher X100 dentro de `meshes/` con los nombres:

- `px100_1_base.stl`
- `px100_2_shoulder.stl`
- `px100_3_upper_arm.stl`
- `px100_4_forearm.stl`
- `px100_5_gripper.stl`
- `px100_6_gripper_prop.stl`
- `px100_7_gripper_bar.stl`
- `px100_8_gripper_finger.stl`

En `urdf/` crea el archivo `robot.xacro` con el contenido del modelo cinemático del robot, asegurándote de:

- Declarar `link world`.
- Unir `world` con `link0` mediante un `joint` fijo.
- Crear las articulaciones `waist`, `shoulder`, `elbow`, `wrist`, `gripper`, etc., con sus límites y ejes correctos.
- Usar rutas tipo `package://pincher_description/meshes/...` para las mallas.

---

### 6.3 Launch `display.launch.py`

En `pincher_description/launch/display.launch.py`:

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('pincher_description')

    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.xacro')
    robot_description = Command(['xacro ', xacro_file])

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output='screen'
    )

    rviz_config = os.path.join(pkg_share, 'rviz', 'pincher.rviz')

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher,
        rviz
    ])
```

> El archivo `pincher.rviz` puede guardarse desde RViz una vez que tengas el robot visible (añadiendo `RobotModel`, `Grid`, etc.) y seleccionando **File → Save Config**.

---

### 6.4 Integrar el botón “LANZAR RViz” en la GUI

En la clase `PincherGUI`, el método `launch_rviz` ejecuta el launch anterior:

```python
import subprocess
import threading

class PincherGUI:
    # ...

    def launch_rviz(self):
        """Lanza display.launch.py en un proceso separado."""
        if self.rviz_process:
            return  # ya está corriendo

        def run_launch():
            self.rviz_process = subprocess.Popen(
                ["ros2", "launch", "pincher_description", "display.launch.py"]
            )
            self.rviz_process.wait()
            self.window.after(0, self.on_rviz_closed)

        thread = threading.Thread(target=run_launch, daemon=True)
        thread.start()

        self.rviz_btn.config(state=tk.DISABLED)
        self.stop_rviz_btn.config(state=tk.NORMAL)
        self.rviz_status_label.config(text="RViz ejecutándose", fg="green")

    def stop_rviz(self):
        if self.rviz_process:
            self.rviz_process.terminate()
            self.rviz_process = None
        self.on_rviz_closed()
```

---

## 7. Comprobación final

1. **Robot real se mueve:**  
   - Mueve las articulaciones con sliders o valores numéricos.
   - Ajusta los signos de las articulaciones en el controlador hasta que el movimiento en RViz coincida con el real.

2. **RViz recibe `/joint_states`:**

   ```bash
   ros2 topic echo /joint_states --once
   ```

   Deberías ver un mensaje con los nombres de las articulaciones y sus posiciones actualizadas.

3. **Robot en RViz se mueve sincronizado** al mover el robot real con la GUI.

Si todo esto funciona, el sistema está correctamente integrado y listo para usarse como base en proyectos más avanzados (planificación de trayectorias, `ros2_control`, etc.).

---

## 8. Recursos recomendados

- Documentación oficial de ROS 2 Humble: tutoriales, conceptos de nodos, tópicos y lanzadores.
- Repositorio oficial de DynamixelSDK (Python) de ROBOTIS.
- Extensión ROS para Visual Studio Code, para depuración y navegación por paquetes.

</div>
