import React from 'react';
import { View, Text } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { CommonActions } from '@react-navigation/native';
import { BottomNavigation, useTheme, Badge } from 'react-native-paper'; // Import thêm Badge

// Import các màn hình
import EmployerHome from '../screens/Employer/EmployerHome'; // Đổi tên cho chuẩn
import Login from '../screens/Auth/Login'; // Tạm
import EmployerProfile from '../screens/Employer/EmployerProfile';

// Màn hình giả lập
const MyJobsScreen = () => <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}><Text>Quản lý tin đăng</Text></View>;
const CandidatesScreen = () => <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}><Text>Danh sách ứng viên</Text></View>;

const Tab = createBottomTabNavigator();

export default function EmployerTabs() {
    const theme = useTheme();

    return (
        <Tab.Navigator
            screenOptions={{
                headerShown: false, // Ẩn header mặc định của React Navigation
            }}
            // Custom lại thanh TabBar bằng React Native Paper
            tabBar={({ navigation, state, descriptors, insets }) => (
                <BottomNavigation.Bar
                    navigationState={state}
                    safeAreaInsets={insets}

                    // --- TÙY CHỈNH GIAO DIỆN Ở ĐÂY ---

                    // 1. Hiệu ứng Shifting (Icon phóng to, ẩn chữ khi active)
                    // Set true nếu muốn hiệu ứng động, false nếu muốn hiện chữ cố định
                    shifting={false}

                    // 2. Màu sắc (Lấy từ theme để đồng bộ)
                    activeColor={theme.colors.primary}
                    inactiveColor={theme.colors.onSurfaceVariant}
                    style={{
                        backgroundColor: theme.colors.elevation.level2, // Màu nền chuẩn MD3
                        borderTopWidth: 0,
                        // Nếu muốn bo tròn 2 góc trên cho mềm mại:
                        borderTopLeftRadius: 20,
                        borderTopRightRadius: 20,
                        // Đổ bóng nhẹ
                        elevation: 4,
                    }}

                    // --- LOGIC XỬ LÝ CLICK (GIỮ NGUYÊN) ---
                    onTabPress={({ route, preventDefault }) => {
                        const event = navigation.emit({
                            type: 'tabPress',
                            target: route.key,
                            canPreventDefault: true,
                        });

                        if (event.defaultPrevented) {
                            preventDefault();
                        } else {
                            navigation.dispatch({
                                ...CommonActions.navigate(route.name, route.params),
                                target: state.key,
                            });
                        }
                    }}

                    // --- RENDER ICON & BADGE ---
                    renderIcon={({ route, focused, color }) => {
                        const { options } = descriptors[route.key];
                        if (options.tabBarIcon) {
                            return options.tabBarIcon({ focused, color, size: 24 });
                        }
                        return null;
                    }}

                    // --- LẤY LABEL ---
                    getLabelText={({ route }) => {
                        const { options } = descriptors[route.key];
                        return options.tabBarLabel !== undefined
                            ? options.tabBarLabel
                            : options.title !== undefined
                                ? options.title
                                : route.name;
                    }}
                />
            )}
        >
            {/* TAB 1: DASHBOARD */}
            <Tab.Screen
                name="Dashboard"
                component={EmployerHome}
                options={{
                    tabBarLabel: 'Tổng quan',
                    tabBarIcon: ({ color, size }) => (
                        <MaterialCommunityIcons name="view-dashboard" color={color} size={size} />
                    ),
                }}
            />

            {/* TAB 2: QUẢN LÝ TIN (MY JOBS) */}
            <Tab.Screen
                name="MyJobs"
                component={MyJobsScreen}
                options={{
                    tabBarLabel: 'Tin của tôi',
                    tabBarIcon: ({ color, size }) => (
                        <MaterialCommunityIcons name="briefcase-edit" color={color} size={size} />
                    ),
                }}
            />

            {/* TAB 3: ỨNG VIÊN (CÓ BADGE THÔNG BÁO) */}
            <Tab.Screen
                name="Candidates"
                component={CandidatesScreen}
                options={{
                    tabBarLabel: 'Ứng viên',
                    // Render icon kèm Badge số lượng hồ sơ mới
                    tabBarIcon: ({ color, size }) => (
                        <View>
                            <MaterialCommunityIcons name="account-group" color={color} size={size} />
                            {/* Giả sử có 5 hồ sơ mới chưa xem */}
                            <Badge
                                size={16}
                                style={{ position: 'absolute', top: -4, right: -4 }}
                            >
                                5
                            </Badge>
                        </View>
                    ),
                }}
            />

            {/* TAB 4: CÀI ĐẶT / TÀI KHOẢN */}
            <Tab.Screen
                name="Settings"
                component={EmployerProfile} // Tạm
                options={{
                    tabBarLabel: 'Tài khoản',
                    tabBarIcon: ({ color, size }) => (
                        <MaterialCommunityIcons name="account" color={color} size={size} />
                    ),
                }}
            />
        </Tab.Navigator>
    );
}