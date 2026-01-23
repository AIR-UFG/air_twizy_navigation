"""

A ideia aqui é passar as configuracoes de inicializacao do RTABmap para que ele funcione
diretamente com o nav2, para isso vamos precisar tambem de fazer um novo yaml de config
para o nav2. Baseado no yaml que ja temos como exemplo implementado

"""
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from nav2_common.launch import RewrittenYaml
from launch_ros.actions import Node


def generate_launch_description():
    # Get the launch directory
    bringup_dir = get_package_share_directory('nav2_bringup')

    nav2_rtab_dir = get_package_share_directory(                   
        "nav2-rtab")
    
    params_dir = os.path.join(nav2_rtab_dir, "config")
    nav2_params = os.path.join(params_dir, "nav2_params_localization.yaml")
    map_file = os.path.join(params_dir, "meu_mapa.yaml")
    db_path = os.path.join(params_dir, "sim_env.db")

    configured_params = RewrittenYaml(
        source_file=nav2_params, root_key="", param_rewrites="", convert_types=True
    )

    use_rviz = LaunchConfiguration('use_rviz')

    declare_use_rviz_cmd = DeclareLaunchArgument(
        'use_rviz',
        default_value='False',
        description='Whether to start RVIZ')
    

    navigation2_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", "navigation_launch.py")
        ),
        launch_arguments={
            "use_sim_time": "True",
            "map": map_file,
            "map_type": "occupancy",
            "params_file": configured_params,
            "autostart": "True",
        }.items(),
    )

    rviz_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, "launch", 'rviz_launch.py')),
        condition=IfCondition(use_rviz)
    )

    rtabmap_localization = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        output='screen',
        parameters=[{
            'use_sim_time': True,

            # Frames
            'frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'map_frame_id': 'map',

            # Sensores (LiDAR-only)
            'subscribe_scan_cloud': True,
            'subscribe_rgb': False,
            'subscribe_depth': False,
            'approx_sync': True,

            # ====== MODO LOCALIZAÇÃO ======
            'Mem/IncrementalMemory': 'false',
            'Mem/InitWMWithAllNodes': 'true',
            'RGBD/LocalLoopDetection': 'false',

            # ====== NÃO CRIAR MAPA ======
            'RGBD/CreateOccupancyGrid': 'false',
            'Grid/3D': 'false',

            # ====== ICP ======
            'Reg/Force3DoF': 'true',
            'Reg/Strategy': '1',

            'Icp/PointToPlane': 'true',
            'Icp/Iterations': '10',
            'Icp/VoxelSize': '0.1',
            'Icp/MaxCorrespondenceDistance': '1.0',

            # ====== DB EXISTENTE ======
            'database_path': db_path
        }],
        remappings=[
            ('scan_cloud', 'odom_filtered_input_scan')
        ]
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
    
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'yaml_filename': map_file 
        }]
    )

    lifecycle_map_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': ['map_server']
        }]
    )
    
    # Create the launch description and populate
    ld = LaunchDescription()

    #RTAB launch
    ld.add_action(rtabmap_odom)
    ld.add_action(rtabmap_localization)
    #ld.add_action(rtabmap_viz)

    ld.add_action(map_server)
    ld.add_action(lifecycle_map_manager)

    # navigation2 launch
    ld.add_action(navigation2_cmd)

    # viz launch
    ld.add_action(declare_use_rviz_cmd)
    ld.add_action(rviz_cmd)
    return ld
