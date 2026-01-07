import styles from "../styles/Candidate/CandidateJobDetailStyles";
import {TouchableOpacity, View} from "react-native";
import React from "react";
import {MaterialCommunityIcons} from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';

const CustomHeader = ({ navigation }) => {
    // const navigation = useNavigation();
    return (
        <View style={styles.headerNav}>
            <TouchableOpacity onPress={() => navigation?.canGoBack() ? navigation.goBack() : null}>
                <MaterialCommunityIcons name="arrow-left" size={24} color="#1A1D1F"/>
            </TouchableOpacity>
            <TouchableOpacity>
                <MaterialCommunityIcons name="dots-horizontal" size={24} color="#1A1D1F"/>
            </TouchableOpacity>
        </View>
    );
};

export default CustomHeader