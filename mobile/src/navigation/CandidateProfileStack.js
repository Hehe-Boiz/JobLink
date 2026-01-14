import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';

import CandidateProfile from '../screens/CandidateProfile/CandidateProfile';
import LanguageList from '../screens/CandidateProfile/LanguageList';
import AddLanguage from '../screens/CandidateProfile/AddLanguage';
import LanguageDetail from '../screens/CandidateProfile/LanguageDetail';

const Stack = createStackNavigator();

export default function CandidateProfileStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="CandidateProfileMain" component={CandidateProfile} />
      <Stack.Screen name="LanguageList" component={LanguageList} />
      <Stack.Screen name="AddLanguage" component={AddLanguage} />
      <Stack.Screen name="LanguageDetail" component={LanguageDetail} />
    </Stack.Navigator>
  );
}
