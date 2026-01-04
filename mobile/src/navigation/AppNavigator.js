// src/navigation/AppNavigator.js
import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';

// Import các màn hình Auth
import Login from '../screens/Auth/Login';
// Import bộ Tab vừa làm
import EmployerTabs from './EmployerTabs';
import {Provider} from 'react-native-paper';
import Register from '../screens/Auth/Register';

const Stack = createStackNavigator();

export default function AppNavigator() {
    const isAuthenticated = true; // Giả lập đã đăng nhập
    const userRole = 'Employer'; // Giả lập role

    return (
        <Provider>
            <NavigationContainer>
                <Stack.Navigator screenOptions={{headerShown: false}}>
                    {!isAuthenticated ? (
                        // Stack cho người chưa đăng nhập
                        <>
                            <Stack.Screen name="Login" component={Login}/>
                            <Stack.Screen name="Register" component={Register}/>
                        </>
                    ) : (
                        // Stack cho người đã đăng nhập
                        <>
                            {userRole === 'Employer' ? (
                                <Stack.Screen name="EmployerMain" component={EmployerTabs}/>
                            ) : (
                                <Stack.Screen name="CandidateMain" component={CandidateTabs}/>
                            )}
                        </>
                    )}
                </Stack.Navigator>
            </NavigationContainer>
        </Provider>
    );
}