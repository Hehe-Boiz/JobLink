import React from 'react';
import { View, Text } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { BottomNavigation, useTheme, Badge } from 'react-native-paper'; // Import thêm Badge

// Import các màn hình
import EmployerHome from '../screens/Employer/EmployerHome'; // Đổi tên cho chuẩn
import Login from '../screens/Auth/Login'; // Tạm
import EmployerProfile from '../screens/Employer/EmployerProfile';
import styles from '../styles/Employer/EmployerTabStyles';
// Màn hình giả lập
const MyJobsScreen = () => <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}><Text>Quản lý tin đăng</Text></View>;
const CandidatesScreen = () => <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}><Text>Danh sách ứng viên</Text></View>;

const Tab = createBottomTabNavigator();

export default function EmployerTabs() {
    const theme = useTheme();

    return (
        <Tab.Navigator
            screenOptions={{
                headerShown: false,
                tabBarActiveTintColor: '#0D0140',
                tabBarInactiveTintColor: '#95969D',
                tabBarShowLabel: false,
                tabBarStyle: {
                    backgroundColor: '#fff',
                    borderTopWidth: 0,
                    elevation: 10,
                    shadowColor: '#000',
                    shadowOffset: { width: 0, height: -3 },
                    shadowOpacity: 0.1,
                    shadowRadius: 8,
                    height: 70,
                    paddingBottom: 10,
                    paddingTop: 10,
                },
            }}
        >
            <Tab.Screen
                name="Home"
                component={EmployerHome}
                options={{
                    tabBarIcon: ({ color, size, focused }) => (
                        <View style={focused ? styles.activeTab : null}>
                            <MaterialCommunityIcons name="view-dashboard" size={28} color={color} />
                        </View>
                    ),
                }}
            />

            <Tab.Screen
                name="MyJobs"
                component={MyJobsScreen}
                options={{
                    tabBarIcon: ({ color, size, focused }) => (
                        <View style={focused ? styles.activeTab : null}>
                            <MaterialCommunityIcons name="briefcase-edit" size={28} color={color} />
                        </View>
                    ),
                }}
            />

            <Tab.Screen
                name="AddJob"
                component={Login}
                options={{
                    tabBarIcon: ({ focused }) => (
                        <View style={styles.addButton}>
                            <MaterialCommunityIcons name="plus" size={32} color="#fff" />
                        </View>
                    ),
                }}
            />

            <Tab.Screen
                name="Candidates"
                component={CandidatesScreen}
                options={{
                    tabBarIcon: ({ color, size, focused }) => (
                        <View style={focused ? styles.activeTab : null}>
                            <MaterialCommunityIcons name="account-group" size={28} color={color} />
                        </View>
                    ),
                }}
            />

            <Tab.Screen
                name="Profile"
                component={EmployerProfile}
                options={{
                    tabBarIcon: ({ color, size, focused }) => (
                        <View style={focused ? styles.activeTab : null}>
                            <MaterialCommunityIcons name="account-outline" size={28} color={color} />
                        </View>
                    ),
                }}
            />
        </Tab.Navigator>
    );
}