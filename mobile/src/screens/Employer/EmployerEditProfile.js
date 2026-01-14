import React, { useState, useContext, useEffect } from 'react';
import { View, Text, ScrollView, Image, TouchableOpacity, Alert, Platform, KeyboardAvoidingView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { TextInput, Button, ActivityIndicator } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';

import styles from '../../styles/Employer/EmployerStyles';
import { MyUserContext } from '../../utils/contexts/MyContext';
import Apis, { authApis, endpoints } from '../../utils/Apis';
import { useDialog } from '../../hooks/useDialog';
import { useEmployer } from '../../hooks/useEmployer';

const EmployerEditProfile = ({ navigation }) => {
    const [user, dispatch] = useContext(MyUserContext);
    const { showDialog } = useDialog();
    const [loading, setLoading] = useState(false);
    const { profile, dispatch: empDispatch } = useEmployer();
    const [avatar, setAvatar] = useState(null);

    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        phone: '',
        company_name: '',
        website: '',
        tax_code: ''
    });

    useEffect(() => {
        try {
            setLoading(true);
            setAvatar({ uri: user.avatar });
            setFormData(prev => ({
                ...prev,
                first_name: user.first_name,
                last_name: user.last_name,
                phone: user.phone || '',
            }));
            if (profile) {
                setFormData(prev => ({
                    ...prev,
                    company_name: profile.company_name || '',
                    website: profile.website || '',
                    tax_code: profile.tax_code || ''
                }));
            }
        } catch (ex) {
            console.log("Load profile error:", ex);
        }finally{
            setLoading(false);
        }
    }, [profile]);

    // 2. Hàm chọn ảnh
    const pickImage = async () => {
        let result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ImagePicker.Images,
            allowsEditing: true,
            aspect: [1, 1],
            quality: 1,
        });

        if (!result.canceled) {
            setAvatar(result.assets[0]);
        }
    };

    // Helper đổi text
    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    // 3. Hàm Lưu thay đổi
    const handleSave = async () => {
        setLoading(true);
        try {
            const token = await AsyncStorage.getItem('token');
            const api = authApis(token);

            let userForm = new FormData();
            userForm.append('first_name', formData.first_name);
            userForm.append('last_name', formData.last_name);
            userForm.append('phone', formData.phone);

            if (avatar && !avatar.uri.startsWith('http')) {
                let filename = avatar.uri.split('/').pop();
                let match = /\.(\w+)$/.exec(filename);
                let type = match ? `image/${match[1]}` : `image`;

                userForm.append('avatar', {
                    uri: avatar.uri,
                    name: filename,
                    type: type,
                });
            }

            let userRes = await api.patch(endpoints['current_user'], userForm, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            dispatch({
                type: "login",
                payload: userRes.data
            });

            let updatedData = {
                company_name: formData.company_name,
                website: formData.website,
                tax_code: formData.tax_code
            };
            await api.patch(endpoints['current_employer'], updatedData);
            empDispatch({
                type: "UPDATE_PROFILE",
                payload: updatedData
            });
            showDialog({
                type: 'success',
                title: 'Thành công',
                content: 'Hồ sơ đã được cập nhật!',
                onConfirm: () => navigation.goBack()
            });

        } catch (ex) {
            console.error(ex);
            showDialog({
                type: 'error',
                title: 'Lỗi',
                content: 'Cập nhật thất bại. Vui lòng thử lại.'
            });
        } finally {
            setLoading(false);
        }
    };
    if (loading) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F5F7FA' }}>
                <ActivityIndicator size="large" color="#130160" />
                <Text style={{ marginTop: 10, color: '#524B6B' }}>Đang tải thông tin...</Text>
            </View>
        );
    }
    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={{ flex: 1 }}>

                {/* Header */}
                <View style={styles.header}>
                    <TouchableOpacity onPress={() => navigation.goBack()}>
                        <MaterialCommunityIcons name="arrow-left" size={24} color="#130160" />
                    </TouchableOpacity>
                    <Text style={styles.headerTitle}>Chỉnh sửa hồ sơ</Text>
                    <View style={{ width: 24 }} />
                </View>

                <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>

                    {/* Avatar Upload */}
                    <View style={styles.editAvatarContainer}>
                        <TouchableOpacity onPress={pickImage}>
                            <Image
                                source={{ uri: avatar?.uri }}
                                style={styles.editAvatar}
                            />
                            <View style={styles.cameraBtn}>
                                <MaterialCommunityIcons name="camera" size={20} color="white" />
                            </View>
                        </TouchableOpacity>
                        <Text style={{ marginTop: 10, color: '#95969D', fontSize: 13 }}>Chạm để đổi ảnh đại diện</Text>
                    </View>

                    {/* Phần 1: Thông tin cá nhân */}
                    <View style={{ paddingHorizontal: 20 }}>
                        <View style={styles.formSection}>
                            <Text style={styles.formTitle}>Thông tin cá nhân</Text>

                            <TextInput
                                label="Họ (Last Name)"
                                value={formData.last_name}
                                onChangeText={(t) => handleChange('last_name', t)}
                                style={styles.input} mode="outlined" outlineColor="#EAEAEA" activeOutlineColor="#130160"
                            />
                            <View style={{ height: 15 }} />
                            <TextInput
                                label="Tên (First Name)"
                                value={formData.first_name}
                                onChangeText={(t) => handleChange('first_name', t)}
                                style={styles.input} mode="outlined" outlineColor="#EAEAEA" activeOutlineColor="#130160"
                            />
                            <View style={{ height: 15 }} />
                            <TextInput
                                label="Số điện thoại"
                                value={formData.phone}
                                onChangeText={(t) => handleChange('phone', t)}
                                keyboardType="phone-pad"
                                style={styles.input} mode="outlined" outlineColor="#EAEAEA" activeOutlineColor="#130160"
                            />
                        </View>

                        {/* Phần 2: Thông tin công ty */}
                        <View style={styles.formSection}>
                            <Text style={styles.formTitle}>Thông tin công ty</Text>

                            <TextInput
                                label="Tên công ty"
                                value={formData.company_name}
                                onChangeText={(t) => handleChange('company_name', t)}
                                style={styles.input} mode="outlined" outlineColor="#EAEAEA" activeOutlineColor="#130160"
                            />
                            <View style={{ height: 15 }} />
                            <TextInput
                                label="Mã số thuế"
                                value={formData.tax_code}
                                onChangeText={(t) => handleChange('tax_code', t)}
                                style={styles.input} mode="outlined" outlineColor="#EAEAEA" activeOutlineColor="#130160"
                            />
                            <View style={{ height: 15 }} />
                            <TextInput
                                label="Website"
                                value={formData.website}
                                onChangeText={(t) => handleChange('website', t)}
                                style={styles.input} mode="outlined" outlineColor="#EAEAEA" activeOutlineColor="#130160"
                            />
                        </View>

                        {/* Nút Save */}
                        <Button
                            mode="contained"
                            onPress={handleSave}
                            loading={loading}
                            disabled={loading}
                            style={styles.btnPrimary}
                            labelStyle={{ fontSize: 16, fontWeight: 'bold' }}
                        >
                            LƯU THAY ĐỔI
                        </Button>
                    </View>

                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
};

export default EmployerEditProfile;