"""

A ideia aqui é passar as configuracoes de inicializacao do RTABmap para que ele funcione
diretamente com o nav2, para isso vamos precisar tambem de fazer um novo yaml de config
para o nav2. Baseado no yaml que ja temos como exemplo implementado

"""
import os
import xacro

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from nav2_common.launch import RewrittenYaml
from launch_ros.actions import Node


def generate_launch_description():

    real_agr = DeclareLaunchArgument(
        'real',
        default_value='false',
        description='whether to use in sim or real context'
    )

    dir_shared_path = get_package_share_directory("nav2-rtab")
    rviz_file = os.path.join(dir_shared_path, 'config', 'slam_view.rviz')

    description_share_path = get_package_share_directory('air_description')
    xacro_file = os.path.join(description_share_path, 'urdf', 'sd_twizy.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    robot_urdf = robot_description_config.toxml()

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_urdf}],
        condition=IfCondition(LaunchConfiguration('real'))
    )
  
    rtabmap_odom = Node(
        package='rtabmap_odom', executable='icp_odometry', output='screen',
        parameters=[{
            'use_sim_time':True,
            'frame_id':'base_link',
            'odom_frame_id':'odom',
            'wait_for_transform':0.2,
            'expected_update_rate':15.0,
            'deskewing':False,
            # RTAB-Map's internal parameters are strings:
            'Icp/PointToPlane': 'true',
            'Icp/Iterations': '10',
            'Icp/VoxelSize': '0.1',
            'Icp/Epsilon': '0.001',
            'Icp/PointToPlaneK': '20',
            'Icp/PointToPlaneRadius': '0',
            'Icp/MaxTranslation': '2',
            'Icp/MaxCorrespondenceDistance': '1',
            'Icp/Strategy': '1',
            'Icp/OutlierRatio': '0.7',
            'Icp/CorrespondenceRatio': '0.01',
            'Odom/ScanKeyFrameThr': '0.4',
            'OdomF2M/ScanSubtractRadius': '0.1',
            'OdomF2M/ScanMaxSize': '15000',
            'OdomF2M/BundleAdjustment': 'false'
        }],
        remappings=[
            ('scan_cloud', '/velodyne_points')
        ])
    
    rtabmap_slam = Node(
        package='rtabmap_slam', executable='rtabmap', output='screen',
        parameters=[{
            'frame_id':'base_link',
            'subscribe_depth':False,
            'subscribe_rgb':False,
            'subscribe_scan_cloud':True,
            'approx_sync':True,
            'wait_for_transform':0.2,
            'use_sim_time':True,

            'Grid/ScanDecimation': '4',

            # 1. PREENCHIMENTO (Resolve os "raios" falhados)
            'Grid/RayTracing': 'true',        # OBRIGATÓRIO: Limpa o espaço vazio até o obstáculo
            'Grid/3D': 'false',               # Força a criação de um mapa 2D achatado
            'Grid/RangeMax': '20.0',          # Alcance máximo confiável (ajuste se precisar)
            'Grid/CellSize': '0.1',           # 10cm. Se estiver 0.05 fica muito ruidoso com LiDAR 3D
            
            # 2. LIDAR COM O CHÃO (Resolve o buraco ao redor do carro)
            # Importante: Como seu LiDAR é 3D, ele bate no chão. Queremos que chão = LIVRE.
            'Grid/NormalsSegmentation': 'true',  # Usa a inclinação para detectar o chão (melhor que altura fixa)
            'Grid/MaxGroundAngle': '45.0',       # Pontos planos são chão. Pontos verticais são paredes.
            'Grid/ClusterRadius': '0.5',         # Filtro de ruído (tamanho do grupo)
            'Grid/MinClusterSize': '3',          # Filtro de ruído: Obstáculo precisa ter 3 pontos para existir
            
            # 3. ALTURA DO OBSTÁCULO (Evita mapear teto ou galhos muito altos)
            # Se o lidar está no teto do carro, cuidado para ele não pegar o teto da garagem como obstáculo
            'Grid/MinObstacleHeight': '-0.281',    # (Relativo ao base_link) Mínimo para ser obstáculo
            'Grid/MaxObstacleHeight': '1.5',

            # RTAB-Map's internal parameters are strings:
            'RGBD/ProximityMaxGraphDepth': '0',
            'RGBD/ProximityPathMaxNeighbors': '1',
            'RGBD/AngularUpdate': '0.05',
            'RGBD/LinearUpdate': '0.05',
            'RGBD/CreateOccupancyGrid': 'true',
            'Mem/NotLinkedNodesKept': 'false',
            'Mem/STMSize': '30',
            'Mem/LaserScanNormalK': '20',
            'Reg/Strategy': '1',
            'Icp/VoxelSize': '0.1',
            'Icp/PointToPlaneK': '20',
            'Icp/PointToPlaneRadius': '0',
            'Icp/PointToPlane': 'true',
            'Icp/Iterations': '10',
            'Icp/Epsilon': '0.001',
            'Icp/MaxTranslation': '3',
            'Icp/MaxCorrespondenceDistance': '1',
            'Icp/Strategy': '1',
            'Icp/OutlierRatio': '0.7',
            'Icp/CorrespondenceRatio': '0.2'
        }],
        remappings=[
            ('scan_cloud', 'odom_filtered_input_scan')
        ],
        arguments=[
            '-d' # This will delete the previous database (~/.ros/rtabmap.db)
        ]) 
        
    rtabmap_viz = Node(
        package='rtabmap_viz', executable='rtabmap_viz', output='screen',
        parameters=[{
            'use_sim_time':True,
            'frame_id':'base_link',
            'odom_frame_id':'odom',
            'subscribe_odom_info':True,
            'subscribe_scan_cloud':True,
            'approx_sync':False,
        }],
        remappings=[
            ('scan_cloud', 'odom_filtered_input_scan')
        ])
    
    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_file]
    )
    
    # Create the launch description and populate
    ld = LaunchDescription()

    #RTAB launch
    ld.add_action(rtabmap_odom)
    ld.add_action(rtabmap_slam)
    ld.add_action(rtabmap_viz)

    # launch rviz
    ld.add_action(rviz2_node)

    return ld
