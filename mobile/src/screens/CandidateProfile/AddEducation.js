import React, {useState, useMemo} from 'react';
import {
    View,
    TouchableOpacity,
    KeyboardAvoidingView,
    Platform,
    TouchableWithoutFeedback,
    Keyboard,
    ScrollView,
    TextInput,
    ActivityIndicator, Alert
} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import CustomText from '../../components/common/CustomText';
import ConfirmationSheet from '../../components/common/ConfirmationSheet';
import CustomSelector from '../../components/common/CustomSelector';
import styles from '../../styles/CandidateProfile/AddWorkExperienceStyles';
import {authApis, endpoints} from '../../utils/Apis';
import MonthYearInput from '../../components/common/MonthYear/MonthYearInput';
import AsyncStorage from "@react-native-async-storage/async-storage";

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const parseDateToPickerValue = (dateInput) => {
    if (!dateInput || dateInput === 'Present') return null;
    const d = new Date(dateInput);
    if (isNaN(d.getTime())) return null;
    return {
        month: MONTHS[d.getMonth()],
        year: d.getFullYear()
    };
};

const formatDateForBackend = (pickerValue) => {
    if (!pickerValue) return null;
    const monthIndex = MONTHS.indexOf(pickerValue.month) + 1;
    const monthStr = monthIndex < 10 ? `0${monthIndex}` : monthIndex;
    return `${pickerValue.year}-${monthStr}-01`;
};


const AddEducation = ({navigation, route}) => {
    const {education, isEdit} = route.params || {};

    const INSTITUTION_LIST = [
        {id: '1', name: 'University of Oxford'},
        {id: '2', name: 'Harvard University'},
        {id: '3', name: 'MIT'},
        {id: '4', name: 'Stanford University'},
        {id: '5', name: 'University of Cambridge'},
        {id: '6', name: 'National University of Singapore'},
        {id: 'OTHER_OPTION', name: 'Other / Tự nhập trường khác'}
    ];
    const LEVEL_LIST = [
        {id: '1', name: 'High School Diploma'},
        {id: '2', name: 'Associate Degree'},
        {id: '3', name: 'Bachelor\'s Degree'},
        {id: '4', name: 'Master\'s Degree'},
        {id: '5', name: 'Ph.D.'},
        {id: 'OTHER_OPTION', name: 'Other / Tự nhập cấp bậc khác'}
    ];

    const initialData = useMemo(() => {
        if (!isEdit || !education) return {};

        let initLevel = '';
        let initField = education.degree || '';

        if (education.degree && education.degree.includes(' - ')) {
            const parts = education.degree.split(' - ');
            initLevel = parts[0];
            initField = parts.slice(1).join(' - ');
        } else {
            const matchLevel = LEVEL_LIST.find(l => education.degree.startsWith(l.name));
            if (matchLevel) {
                initLevel = matchLevel.name;
                initField = education.degree.replace(matchLevel.name, '').trim().replace(/^- /, '');
            } else {
                initField = education.degree;
            }
        }

        const isCurrent = education.endDate === 'Present' || (!education.endDate && !!education.startDate);

        return {
            institution: education.school || '',
            level: initLevel,
            fieldOfStudy: initField,
            startDate: education.startDate,
            endDate: education.endDate,
            description: education.description || '',
            isCurrentPosition: isCurrent
        };
    }, [education, isEdit]);

    const [formData, setFormData] = useState({
        level: initialData.level || '',
        institution: initialData.institution || '',
        fieldOfStudy: initialData.fieldOfStudy || '',
        startDate: parseDateToPickerValue(initialData.startDate),
        endDate: parseDateToPickerValue(initialData.endDate),
        description: initialData.description || '',
    });

    const [isCurrentPosition, setIsCurrentPosition] = useState(
        initialData.isCurrentPosition || false
    );

    const [loading, setLoading] = useState(false);
    const [showSheet, setShowSheet] = useState(false);
    const [sheetType, setSheetType] = useState('undo');

    const isInstitutionInList = (val) => INSTITUTION_LIST.some(item => item.name === val);
    const [isManualInstitution, setIsManualInstitution] = useState(
        !!initialData.institution && !isInstitutionInList(initialData.institution)
    );

    const isLevelInList = (val) => LEVEL_LIST.some(item => item.name === val);
    const [isManualLevel, setIsManualLevel] = useState(
        !!initialData.level && !isLevelInList(initialData.level)
    );


    const handleChange = (field, value) => {
        setFormData(prev => ({...prev, [field]: value}));
    };

    const handleInstitutionSelect = (item) => {
        if (!item) {
            handleChange('institution', '');
            return;
        }
        if (item.id === 'OTHER_OPTION') {
            setIsManualInstitution(true);
            handleChange('institution', '');
        } else {
            handleChange('institution', item.name);
            setIsManualInstitution(false);
        }
    };

    const handleLevelSelect = (item) => {
        if (!item) {
            handleChange('level', '');
            return;
        }
        if (item.id === 'OTHER_OPTION') {
            setIsManualLevel(true);
            handleChange('level', '');
        } else {
            handleChange('level', item.name);
            setIsManualLevel(false);
        }
    };

    const handleToggleCurrentPosition = () => {
        const newValue = !isCurrentPosition;
        setIsCurrentPosition(newValue);
        if (newValue) {
            handleChange('endDate', null);
        }
    };

    const checkHasChanges = () => {
        const currentLevel = formData.level || '';
        const initialLevel = initialData.level || '';
        const currentInstitution = formData.institution || '';
        const initialInstitution = initialData.institution || '';
        const currentField = formData.fieldOfStudy || '';
        const initialField = initialData.fieldOfStudy || '';
        const currentDesc = formData.description || '';
        const initialDesc = initialData.description || '';

        const currentStart = JSON.stringify(formData.startDate);
        const initialStart = JSON.stringify(parseDateToPickerValue(initialData.startDate));

        const currentEnd = JSON.stringify(formData.endDate);
        const initialEnd = JSON.stringify(parseDateToPickerValue(initialData.endDate));

        return (
            currentLevel !== initialLevel ||
            currentInstitution !== initialInstitution ||
            currentField !== initialField ||
            currentDesc !== initialDesc ||
            currentStart !== initialStart ||
            currentEnd !== initialEnd ||
            isCurrentPosition !== (initialData.isCurrentPosition || false)
        );
    };

    const handleSave = async () => {
        if (!formData.institution.trim() || !formData.fieldOfStudy.trim()) {
            Alert.alert("Missing Information", "Please enter Institution and Field of Study.");
            return;
        }
        if (!formData.startDate) {
            Alert.alert("Missing Information", "Please select Start Date.");
            return;
        }

        try {
            setLoading(true);
            const token = await AsyncStorage.getItem('token');
            const api = authApis(token);

            const finalDegree = formData.level
                ? `${formData.level} - ${formData.fieldOfStudy}`
                : formData.fieldOfStudy;

            const payload = {
                institution: formData.institution,
                level: formData.level,
                field_of_study: formData.fieldOfStudy,
                start_date: formatDateForBackend(formData.startDate),
                end_date: isCurrentPosition ? null : formatDateForBackend(formData.endDate),
                is_current: isCurrentPosition,
                description: formData.description
            };

            if (isEdit) {
                await api.patch(`${endpoints.education}${education.id}/`, payload);
            } else {
                await api.post(endpoints.education, payload);
            }

            navigation.goBack();

        } catch (error) {
            console.error("Save error:", error);
            const errorMsg = error.response?.data
                ? JSON.stringify(error.response.data)
                : "Failed to save education details.";
            Alert.alert("Error", errorMsg);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!isEdit || !education?.id) return;

        setSheetType('remove');
        setShowSheet(true);
    };


    const handleBack = () => {
        if (checkHasChanges()) {
            Keyboard.dismiss();
            setSheetType('undo');
            setShowSheet(true);
        } else {
            navigation.goBack();
        }
    };

    const onConfirmAction = async () => {
        setShowSheet(false);

        if (sheetType === 'undo') {
            navigation.goBack();
        } else if (sheetType === 'remove') {
            try {
                setLoading(true);
                const token = await AsyncStorage.getItem('token');

                await authApis(token).delete(`${endpoints.education}${education.id}/`);

                navigation.goBack();
            } catch (error) {
                console.error("Delete error:", error);
                Alert.alert("Error", "Could not delete education.");
            } finally {
                setLoading(false);
            }
        }
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
            <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.keyboardView}>
                <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
                    <View style={styles.content}>

                        <View style={{flexDirection: 'row', alignItems: 'center', marginTop: 10}}>
                            <TouchableOpacity onPress={handleBack} style={styles.backButton}>
                                <MaterialCommunityIcons name="arrow-left" size={28} color="#150B3D"/>
                            </TouchableOpacity>
                            <CustomText style={[styles.title, {
                                marginBottom: 0,
                                flex: 1,
                                textAlign: 'center',
                                marginRight: 44
                            }]}>
                                {isEdit ? 'Change Education' : 'Add Education'}
                            </CustomText>
                        </View>

                        <ScrollView showsVerticalScrollIndicator={false}
                                    contentContainerStyle={[styles.scrollContent, {paddingTop: 20}]}>
                            {isManualLevel ? (
                                <View style={{marginBottom: 15}}>
                                    <View style={styles.inputGroup}>
                                        <CustomText style={styles.label}>Level of education</CustomText>
                                        <TextInput
                                            style={styles.input}
                                            value={formData.level}
                                            onChangeText={(val) => handleChange('level', val)}
                                            placeholder="Enter your level (e.g. Bachelor)"
                                            placeholderTextColor="#AAA6B9"
                                        />
                                    </View>
                                    <TouchableOpacity
                                        onPress={() => setIsManualLevel(false)}
                                        style={{alignSelf: 'flex-end', marginTop: 0}}
                                    >
                                        <CustomText
                                            style={{color: '#130160', fontSize: 13, textDecorationLine: 'underline'}}>
                                            Select from list
                                        </CustomText>
                                    </TouchableOpacity>
                                </View>
                            ) : (
                                <View style={{marginBottom: 15}}>
                                    <CustomSelector
                                        label="Level of education"
                                        placeholder="Select Level"
                                        data={LEVEL_LIST}
                                        selectedValue={LEVEL_LIST.find(i => i.name === formData.level)}
                                        onSelect={handleLevelSelect}
                                    />
                                </View>
                            )}

                            {isManualInstitution ? (
                                <View style={{marginBottom: 15}}>
                                    <View style={styles.inputGroup}>
                                        <CustomText style={styles.label}>Institution name</CustomText>
                                        <TextInput
                                            style={styles.input}
                                            value={formData.institution}
                                            onChangeText={(val) => handleChange('institution', val)}
                                            placeholder="Enter your institution name"
                                            placeholderTextColor="#AAA6B9"
                                        />
                                    </View>
                                    <TouchableOpacity
                                        onPress={() => setIsManualInstitution(false)}
                                        style={{alignSelf: 'flex-end', marginTop: 0}}
                                    >
                                        <CustomText
                                            style={{color: '#130160', fontSize: 13, textDecorationLine: 'underline'}}>
                                            Select from list
                                        </CustomText>
                                    </TouchableOpacity>
                                </View>
                            ) : (
                                <View style={{marginBottom: 15}}>
                                    <CustomSelector
                                        label="Institution name"
                                        placeholder="Select Institution"
                                        data={INSTITUTION_LIST}
                                        selectedValue={INSTITUTION_LIST.find(i => i.name === formData.institution)}
                                        onSelect={handleInstitutionSelect}
                                    />
                                </View>
                            )}

                            <View style={styles.inputGroup}>
                                <CustomText style={styles.label}>Field of study</CustomText>
                                <TextInput
                                    style={styles.input}
                                    value={formData.fieldOfStudy}
                                    onChangeText={(val) => handleChange('fieldOfStudy', val)}
                                    placeholder="e.g. Information Technology"
                                    placeholderTextColor="#AAA6B9"
                                />
                            </View>

                            <View style={styles.dateRow}>
                                <View style={{flex: 1, marginRight: 10}}>
                                    <MonthYearInput
                                        label="Start date"
                                        value={formData.startDate}
                                        onChange={(val) => handleChange('startDate', val)}
                                        placeholder="Select Date"
                                    />
                                </View>

                                <View style={{flex: 1, marginLeft: 10}}>
                                    {isCurrentPosition ? (
                                        <View>
                                            <CustomText style={styles.label}>End date</CustomText>
                                            <View style={[styles.input, {
                                                backgroundColor: '#F9F9F9',
                                                justifyContent: 'center'
                                            }]}>
                                                <CustomText style={styles.dateTextDisabled}>
                                                    Present
                                                </CustomText>
                                            </View>
                                        </View>
                                    ) : (
                                        <MonthYearInput
                                            label="End date"
                                            value={formData.endDate}
                                            onChange={(val) => handleChange('endDate', val)}
                                            placeholder="Select Date"
                                        />
                                    )}
                                </View>
                            </View>

                            <TouchableOpacity
                                style={styles.checkboxRow}
                                onPress={handleToggleCurrentPosition}
                                activeOpacity={0.8}
                            >
                                <View style={[styles.checkbox, isCurrentPosition && styles.checkboxChecked]}>
                                    {isCurrentPosition && (
                                        <MaterialCommunityIcons name="check" size={14} color="#FFF"/>
                                    )}
                                </View>
                                <CustomText style={styles.checkboxLabel}>This is my position now</CustomText>
                            </TouchableOpacity>

                            <View style={styles.inputGroup}>
                                <CustomText style={styles.label}>Description</CustomText>
                                <View style={styles.textAreaContainer}>
                                    <TextInput
                                        style={styles.textArea}
                                        value={formData.description}
                                        onChangeText={(val) => handleChange('description', val)}
                                        placeholder="Write additional information here"
                                        placeholderTextColor="#AAA6B9"
                                        multiline
                                        textAlignVertical="top"
                                    />
                                </View>
                            </View>

                        </ScrollView>

                        <View style={[styles.buttonContainer, {marginBottom: 0}]}>
                            {isEdit && (
                                <TouchableOpacity style={styles.removeButton} onPress={handleDelete} disabled={loading}>
                                    <CustomText style={styles.removeButtonText}>REMOVE</CustomText>
                                </TouchableOpacity>
                            )}
                            <TouchableOpacity style={styles.saveButton} onPress={handleSave} disabled={loading}>
                                {loading ? (
                                    <ActivityIndicator color="#FFF"/>
                                ) : (
                                    <CustomText style={styles.saveButtonText}>SAVE</CustomText>
                                )}
                            </TouchableOpacity>
                        </View>
                    </View>
                </TouchableWithoutFeedback>
            </KeyboardAvoidingView>

            <ConfirmationSheet
                visible={showSheet}
                type={sheetType}
                onClose={() => setShowSheet(false)}
                onConfirm={onConfirmAction}
            />
        </SafeAreaView>
    );
};

export default AddEducation;