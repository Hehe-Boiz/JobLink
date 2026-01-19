import React, {useState} from 'react';
import {
    View,
    StyleSheet,
    TouchableOpacity,
    TextInput,
    ScrollView,
    Image,
    KeyboardAvoidingView,
    Platform, Alert, ActivityIndicator
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import BgHeader from '../../../assets/images/Background_1.svg';
import CustomSelector from "../../components/common/CustomSelector";
import DayMonthYearInput from "../../components/common/DayMonthYear/DayMonthYearInput";
import {authApis, endpoints} from '../../utils/Apis';
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as ImagePicker from 'expo-image-picker';

const PHONE_CODES = [
    {id: 1, name: '+1 (US/CA)', code: '+1'},
    {id: 2, name: '+84 (VN)', code: '+84'},
    {id: 3, name: '+81 (JP)', code: '+81'},
    {id: 4, name: '+82 (KR)', code: '+82'},
    {id: 5, name: '+65 (SG)', code: '+65'},
];

const getMonthNumber = (mon) => {
    const months = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
        'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    };
    return months[mon] || '01';
}

const getMonthName = (num) => {
    const map = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
        '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
    };
    const paddedNum = num.toString().padStart(2, '0');
    return map[paddedNum] || 'Jan';
};


const EditProfile = ({navigation, route}) => {
    const initial = route?.params?.data || {};
    const [loading, setLoading] = useState(false);

    const [form, setForm] = useState({
        fullName: initial.fullName || '',
        dobRaw: initial.dob || null,
        gender: initial.gender ? initial.gender.toLowerCase() : null,
        email: initial.email || '',
        phone: initial.phone || '',
        location: initial.location || '',
        avatar: initial.avatar || null,
    });

    const [phoneCodeItem, setPhoneCodeItem] = useState(() => {
        const found = PHONE_CODES.find(x => x.code === (initial.phoneCode ?? '+1'));
        return found ? {id: found.id, name: found.name} : {id: 1, name: '+1 (US/CA)'};
    });

    const [dob, setDob] = useState(() => {
        if (initial.dob) {
            const parts = initial.dob.split('-');
            if (parts.length === 3) {
                return {
                    year: parseInt(parts[0]),
                    month: getMonthName(parts[1]),
                    day: parts[2]
                };
            }
        }
        return null;
    });

    const onChangeImage = async () => {
        let result = await ImagePicker.launchImageLibraryAsync({
            mediaTypes: ['images'],
            allowsEditing: true,
            aspect: [1, 1],
            quality: 1,
        });

        if (!result.canceled) {
            setForm(p => ({...p, avatar: result.assets[0].uri}));
        }
    };

    const onSave = async () => {
        setLoading(true);
        try {
            const token = await AsyncStorage.getItem('token');
            const api = authApis(token);
            const userData = new FormData();

            const oldName = initial.fullName || '';
            const newName = form.fullName || '';

            if (newName.trim() !== oldName.trim()) {
                console.log("Phát hiện tên thay đổi, đang cập nhật...");

                const nameParts = newName.trim().split(' ');
                const lastName = nameParts.length > 1 ? nameParts.pop() : '';
                const firstName = nameParts.join(' ');

                userData.append('first_name', lastName);
                userData.append('last_name', firstName);
            }

            if (form.phone !== initial.phone) {
                 userData.append('phone', form.phone);
            }

            if (form.avatar && form.avatar.startsWith('file://')) {
                const filename = form.avatar.split('/').pop();
                const match = /\.(\w+)$/.exec(filename);
                const type = match ? `image/${match[1]}` : `image`;

                userData.append('avatar', {
                    uri: form.avatar,
                    name: filename,
                    type: type,
                });
            }


            const profileData = {
                address: form.location,
            };

            if (form.gender) {
                profileData.gender = form.gender.toUpperCase();
            }

            if (dob) {
                const formattedDob = `${dob.year}-${getMonthNumber(dob.month)}-${dob.day}`;
                profileData.dob = formattedDob;
            }

            console.log("updating profile...");

            const promises = [];

            if (userData._parts && userData._parts.length > 0) {
                 promises.push(api.patch(endpoints.update_user, userData, {
                    headers: { "Content-Type": "multipart/form-data" }
                }));
            }

            promises.push(api.patch(endpoints.update_candidate_profile, profileData));

            await Promise.all(promises);
            Alert.alert("Success", "Profile updated successfully!");

            if (route?.params?.onSave) {
                route.params.onSave();
            }
            navigation.goBack();

        } catch (error) {
            console.error(error);
            let msg = "Update failed";
            if (error.response) {
                console.log(error.response.data);
                msg = JSON.stringify(error.response.data);
            }
            Alert.alert("Error", msg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <SafeAreaView style={styles.container} edges={['left', 'right']}>
            <View style={styles.headerContainer}>
                <BgHeader
                    width="100%"
                    height="400"
                    style={styles.bg}
                    preserveAspectRatio="none"
                />

                <SafeAreaView edges={['top']} style={styles.headerSafe}>
                    {/* Back */}
                    <TouchableOpacity
                        onPress={() => navigation.goBack()}
                        style={styles.backBtn}
                        hitSlop={10}
                        activeOpacity={0.9}
                    >
                        <MaterialCommunityIcons name="arrow-left" size={24} color="#FFF"/>
                    </TouchableOpacity>

                    <View style={styles.rightIcons}>
                        <TouchableOpacity hitSlop={10} activeOpacity={0.9} style={styles.iconBtn}>
                            <MaterialCommunityIcons
                                name="share-variant-outline"
                                size={24}
                                color="#FFF"
                            />
                        </TouchableOpacity>
                        <TouchableOpacity hitSlop={10} activeOpacity={0.9} style={styles.iconBtn}>
                            <MaterialCommunityIcons name="cog-outline" size={24} color="#FFF"/>
                        </TouchableOpacity>
                    </View>

                    <View style={styles.profileBlock}>
                        <Image source={{uri: form.avatar}} style={styles.avatar}/>

                        <View style={styles.infoRow}>
                            <View style={styles.textCol}>
                                <CustomText style={styles.name}>{form.fullName || "User Name"}</CustomText>
                                <CustomText style={styles.locationText}>{form.location || "Location not set"}</CustomText>
                            </View>

                            <TouchableOpacity
                                activeOpacity={0.85}
                                style={styles.changeImgBtn}
                                onPress={onChangeImage}
                            >
                                <CustomText style={styles.changeImgText}>Change image</CustomText>
                            </TouchableOpacity>
                        </View>
                    </View>
                </SafeAreaView>
            </View>

            <KeyboardAvoidingView
                style={{flex: 1}}
                behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            >
                <ScrollView
                    showsVerticalScrollIndicator={false}
                    contentContainerStyle={styles.content}
                >
                    <CustomText style={styles.label}>Fullname</CustomText>
                    <View style={styles.inputWrap}>
                        <TextInput
                            value={form.fullName}
                            onChangeText={(t) => setForm((p) => ({...p, fullName: t}))}
                            style={styles.input}
                            placeholder=""
                            placeholderTextColor="#BDB8CC"
                        />
                    </View>

                    <CustomText style={styles.label}>Date of birth</CustomText>
                    <DayMonthYearInput
                        label={null}
                        value={dob || { day: '', month: '', year: '' }}
                        placeholder="Chưa nhập ngày sinh"
                        onChange={(v) => {
                            setDob(v);
                        }}
                    />

                    <CustomText style={styles.label}>Gender</CustomText>
                    <View style={styles.genderRow}>
                        <TouchableOpacity
                            activeOpacity={0.9}
                            style={[styles.genderBox, form.gender === 'male' && { borderColor: '#FF8A00', backgroundColor: '#FFF5E5' }]}
                            onPress={() => setForm((p) => ({...p, gender: 'male'}))}
                        >
                            <MaterialCommunityIcons
                                name={form.gender === 'male' ? 'radiobox-marked' : 'radiobox-blank'}
                                size={20}
                                color={form.gender === 'male' ? '#FF8A00' : '#CFCFDB'}
                            />
                            <CustomText style={styles.genderText}>Male</CustomText>
                        </TouchableOpacity>

                        <TouchableOpacity
                            activeOpacity={0.9}
                            style={styles.genderBox}
                            onPress={() => setForm((p) => ({...p, gender: 'female'}))}
                        >
                            <MaterialCommunityIcons
                                name={form.gender === 'female' ? 'radiobox-marked' : 'radiobox-blank'}
                                size={20}
                                color={form.gender === 'female' ? '#FF8A00' : '#CFCFDB'}
                            />
                            <CustomText style={styles.genderText}>Female</CustomText>
                        </TouchableOpacity>
                    </View>
                    {!form.gender && (
                         <CustomText style={{fontSize: 12, color: '#999', marginTop: 5, marginLeft: 5}}>
                             * Chưa chọn giới tính
                         </CustomText>
                    )}

                    <CustomText style={styles.label}>Email address</CustomText>
                    <View style={styles.inputWrap}>
                        <TextInput
                            value={form.email}
                            onChangeText={(t) => setForm((p) => ({...p, email: t}))}
                            style={styles.input}
                            placeholder=""
                            placeholderTextColor="#BDB8CC"
                            keyboardType="email-address"
                        />
                    </View>

                    <CustomText style={styles.label}>Phone number</CustomText>
                    <View style={styles.phoneRow}>
                        <View style={{width: 130, marginTop: 5}}>
                            <CustomSelector
                                label={null}
                                placeholder="+Code"
                                data={PHONE_CODES.map(x => ({id: x.id, name: x.name}))}
                                selectedValue={phoneCodeItem}
                                onSelect={(item) => {
                                    setPhoneCodeItem(item);
                                    const picked = PHONE_CODES.find(x => x.id === item?.id);
                                    setForm(p => ({...p, phoneCode: picked?.code ?? p.phoneCode}));
                                }}
                            />
                        </View>


                        <View style={[styles.inputWrap, {flex: 1, marginTop: 0}]}>
                            <TextInput
                                value={form.phone}
                                onChangeText={(t) => setForm((p) => ({...p, phone: t}))}
                                style={styles.input}
                                placeholder=""
                                placeholderTextColor="#BDB8CC"
                                keyboardType="phone-pad"
                            />
                        </View>
                    </View>

                    <CustomText style={styles.label}>Location</CustomText>
                    <View style={styles.inputWrap}>
                        <TextInput
                            value={form.location}
                            onChangeText={(t) => setForm((p) => ({...p, location: t}))}
                            style={styles.input}
                            placeholder=""
                            placeholderTextColor="#BDB8CC"
                        />
                    </View>

                    <View style={{height: 140}}/>
                </ScrollView>

                <View style={styles.footer}>
                    <TouchableOpacity activeOpacity={0.9} style={[styles.saveBtn, loading && {opacity: 0.7}]}
                                      onPress={onSave} disabled={loading}>
                        {loading ? (
                            <ActivityIndicator size="small" color="#FFFFFF"/>
                        ) : (
                            <CustomText style={styles.saveText}>SAVE</CustomText>
                        )}
                    </TouchableOpacity>
                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F6F7FB'
    },

    headerContainer: {
        height: 240,
        width: '100%',
        borderBottomLeftRadius: 22,
        borderBottomRightRadius: 22,
        overflow: 'hidden',
    },
    bg: {
        position: 'absolute',
        top: -30,
        left: 0,
        right: 0,
        bottom: 0,
    },

    headerSafe: {
        flex: 1
    },

    rightIcons: {
        position: 'absolute',
        right: 16,
        top: 40,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 14,
        zIndex: 5,
    },
    backBtn: {
        position: 'absolute',
        left: 13,
        top: 38,
        padding: 8,
        zIndex: 10,
    },
    iconBtn: {
        padding: 8
    },

    profileBlock: {
        position: 'absolute',
        left: 18,
        right: 18,
        bottom: 30,
        alignItems: 'flex-start',
        marginLeft: 15,
    },

    avatar: {
        width: 58,
        height: 58,
        borderRadius: 29,
        borderWidth: 2,
        borderColor: 'rgba(255,255,255,0.25)',
        marginBottom: 10,
    },

    infoRow: {
        width: '100%',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 10,
    },

    textCol: {
        flexShrink: 1,
        minWidth: 0,
        paddingRight: 12,
    },

    name: {
        color: '#FFF',
        fontWeight: '800',
        fontSize: 18
    },
    locationText: {
        color: 'rgba(255,255,255,0.75)',
        fontWeight: '600',
        fontSize: 12,
        marginTop: 4,
    },

    changeImgBtn: {
        backgroundColor: 'rgba(255,255,255,0.16)',
        paddingVertical: 11,
        paddingHorizontal: 16,
        borderRadius: 8,
    },
    changeImgText: {
        color: '#FFF',
        fontSize: 14,
        fontWeight: '500'
    },

    content: {
        paddingHorizontal: 22,
        paddingTop: 16
    },

    label: {
        fontSize: 16,
        fontWeight: '600',
        color: '#150A33',
        marginBottom: 10,
        marginTop: 14,
    },

    inputWrap: {
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        paddingHorizontal: 14,
        paddingVertical: 16,
        borderWidth: 1,
        borderColor: '#ECEAF4',
        height: 57,
        marginBottom: 5
    },

    inputWrapRow: {
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        paddingHorizontal: 14,
        paddingVertical: 12,
        borderWidth: 1,
        borderColor: '#ECEAF4',
        flexDirection: 'row',
        alignItems: 'center',
    },

    input: {
        fontSize: 15,
        color: '#524B6B',
        fontWeight: '400',
        padding: 0
    },

    rightIconBtn: {
        marginLeft: 10,
        padding: 2
    },

    genderRow: {
        flexDirection: 'row',
        gap: 14
    },
    genderBox: {
        flex: 1,
        height: 48,
        borderRadius: 12,
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: '#ECEAF4',
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 14,
    },
    genderText: {
        marginLeft: 10,
        fontWeight: '500',
        color: '#2B2640'
    },

    phoneRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10
    },
    phoneCodeBox: {
        height: 48,
        borderRadius: 12,
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: '#ECEAF4',
        paddingHorizontal: 12,
        flexDirection: 'row',
        alignItems: 'center',
    },
    phoneCodeText: {
        fontWeight: '600',
        color: '#14121F',
        marginRight: 8
    },

    footer: {
        position: 'absolute',
        left: 60,
        right: 60,
        bottom: 22
    },
    saveBtn: {
        height: 54,
        borderRadius: 12,
        backgroundColor: '#130160',
        alignItems: 'center',
        justifyContent: 'center',
    },
    saveText: {
        color: '#FFFFFF',
        fontWeight: '700',
        fontSize: 15.5,
        letterSpacing: 1
    },
});

export default EditProfile;
