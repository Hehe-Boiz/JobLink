import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';
import Login from '../screens/Auth/Login';
import EmployerTabs from './EmployerTabs';
import { Provider } from 'react-native-paper';
import CandidateRegister from '../screens/Auth/CandidateRegister';
import EmployerRegister from '../screens/Auth/EmployerRegister';
import CandidateTabs from './CandidateTabs';
import CandidateDetail from '../screens/Employer/CandidateDetail';
import PostJob from '../screens/Employer/PostJob';
import JobDetail from '../screens/Job/JobDetail';
import ApplyJob from "../screens/Job/ApplyJob";
import CandidateSearchResults from "../screens/Candidate/CandidateSearchResults";
import EmployerEditProfile from '../screens/Employer/EmployerEditProfile';
import CompanyDetail from '../screens/Candidate/CompanyDetail';
import CandidateProfile from "../screens/CandidateProfile/CandidateProfile";
import BuyService from '../screens/Service/BuyService';
import * as Linking from 'expo-linking';

const prefix = Linking.createURL('/')

const Stack = createStackNavigator();

const linking = {
  prefixes: [prefix, 'joblink://'],
  config: {
    screens: {
      // Giả sử bạn muốn mở màn hình 'Home' hoặc màn hình 'PaymentResult' nào đó
      // Nếu bạn muốn xử lý logic chung thì không cần map quá chi tiết
      // Ví dụ map đường dẫn "payment-result" vào màn hình BuyService hoặc Home
      BuyService: 'payment-result', 
    },
  },
};
export default function AppNavigator() {
    const isAuthenticated = true; // Giả lập đã đăng nhập
    const userRole = 'Employer'; // Giả lập role

    return (
        <Provider>
            <NavigationContainer linking={linking}>
                <Stack.Navigator screenOptions={{ headerShown: false }}>
                    <Stack.Screen name="Login" component={Login} />
                    <Stack.Screen name="CandidateRegister" component={CandidateRegister} />
                    <Stack.Screen name="EmployerRegister" component={EmployerRegister} />
                    <Stack.Screen name="EmployerMain" component={EmployerTabs} />
                    <Stack.Screen name="CandidateMain" component={CandidateTabs} />
                    <Stack.Screen name="CandidateDetail" component={CandidateDetail} />
                    <Stack.Screen name="JobDetail" component={JobDetail} />
                    <Stack.Screen name="PostJob" component={PostJob} />
                    <Stack.Screen name="ApplyJob" component={ApplyJob} />
                    <Stack.Screen name="BuyService" component={BuyService} />
                    <Stack.Screen name="CandidateSearchResults" component={CandidateSearchResults} />
                    <Stack.Screen name="EmployerEditProfile" component={EmployerEditProfile} />
                    <Stack.Screen name="CompanyDetail" component={CompanyDetail} />
                    <Stack.Screen name="CandidateProfiles" component={CandidateProfile}/>
                </Stack.Navigator>
            </NavigationContainer>
        </Provider>
    );
}