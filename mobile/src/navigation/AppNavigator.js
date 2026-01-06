// src/navigation/AppNavigator.js
import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';

// Import các màn hình Auth
import Login from '../screens/Auth/Login';
// Import bộ Tab vừa làm
import EmployerTabs from './EmployerTabs';
import { Provider } from 'react-native-paper';
import CandidateRegister from '../screens/Auth/CandidateRegister';
import EmployerRegister from '../screens/Auth/EmployerRegister';
import CandidateTabs from './CandidateTabs';
import JobApplicants from '../screens/Employer/JobApplicants';
import CandidateDetail from '../screens/Employer/CandidateDetail';
import PostJob from '../screens/Employer/PostJob';

const Stack = createStackNavigator();

export default function AppNavigator() {
    const isAuthenticated = true; // Giả lập đã đăng nhập
    const userRole = 'Employer'; // Giả lập role

    return (
        <Provider>
            <NavigationContainer>
                <Stack.Navigator screenOptions={{ headerShown: false }}>
                    <Stack.Screen name="Login" component={Login} />
                    <Stack.Screen name="CandidateRegister" component={CandidateRegister} />
                    <Stack.Screen name="EmployerRegister" component={EmployerRegister} />
                    <Stack.Screen name="EmployerMain" component={EmployerTabs} />
                    <Stack.Screen name="CandidateMain" component={CandidateTabs} />
                    <Stack.Screen name="JobApplicants" component={JobApplicants} />
                    <Stack.Screen name="CandidateDetail" component={CandidateDetail} />
                    <Stack.Screen name="PostJob" component={PostJob} />
                </Stack.Navigator>
            </NavigationContainer>
        </Provider>
    );
}