import React, {useState, useRef, useEffect} from 'react';
import {View, TouchableOpacity, ScrollView, PanResponder, ActivityIndicator} from 'react-native';
import {SafeAreaView} from 'react-native-safe-area-context';
import {MaterialCommunityIcons} from '@expo/vector-icons';
import AsyncStorage from "@react-native-async-storage/async-storage"; // Import thêm
import CustomText from '../../components/common/CustomText';
import CustomFooter from '../../components/common/CustomFooter';
import CustomSelector from '../../components/common/CustomSelector';
import styles from '../../styles/Candidate/CandidateSearchAdvanceStyles';
import stylesJD from '../../styles/Job/JobDetailStyles';
import API, {endpoints} from "../../utils/Apis";

const JOB_TYPES = [
    {id: 'full', label: 'Full time'},
    {id: 'part', label: 'Part time'},
    {id: 'remote', label: 'Remote'},
    {id: 'intern', label: 'Internship'},
];

const UPDATE_TIMES = [
    {id: 'recent', label: 'Recent'},
    {id: 'week', label: 'Last week'},
    {id: 'month', label: 'Last month'},
    {id: 'any', label: 'Any time'},
];

const EXPERIENCE_LEVELS = [
    {id: 'no_experience', label: 'No experience'},
    {id: 'less_than_1', label: 'Less than a year'},
    {id: '1_3', label: '1-3 years'},
    {id: '3_5', label: '3-5 years'},
    {id: '5_10', label: '5-10 years'},
    {id: 'more_than_10', label: 'More than 10 years'},
];

const ResetButton = ({onPress}) => {
    return (
        <TouchableOpacity
            onPress={onPress}
            style={[stylesJD.btnBookmark, stylesJD.resetTextContainer]}
        >
            <CustomText style={stylesJD.resetText}>Reset</CustomText>
        </TouchableOpacity>
    );
};

const RangeSlider = ({min = 0, max = 50, initialLow = 0, initialHigh = 50, onValuesChange, resetTrigger}) => {
    const [sliderWidth, setSliderWidth] = useState(0);
    const [low, setLow] = useState(initialLow);
    const [high, setHigh] = useState(initialHigh);

    useEffect(() => {
        setLow(initialLow);
        setHigh(initialHigh);
    }, [initialLow, initialHigh, resetTrigger]);

    const lowRef = useRef(low);
    const highRef = useRef(high);
    const sliderWidthRef = useRef(sliderWidth);
    const startLowRef = useRef(0);
    const startHighRef = useRef(0);

    useEffect(() => {
        lowRef.current = low;
    }, [low]);
    useEffect(() => {
        highRef.current = high;
    }, [high]);
    useEffect(() => {
        sliderWidthRef.current = sliderWidth;
    }, [sliderWidth]);

    const panLow = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: () => true,
            onPanResponderGrant: () => {
                startLowRef.current = lowRef.current;
            },
            onPanResponderMove: (_, gesture) => {
                const width = sliderWidthRef.current;
                if (!width) return;
                const diff = (gesture.dx / width) * (max - min);
                let newVal = startLowRef.current + diff;
                newVal = Math.max(min, Math.min(newVal, highRef.current - 1));
                const roundedVal = Math.round(newVal);
                if (roundedVal !== lowRef.current) {
                    setLow(roundedVal);
                    onValuesChange && onValuesChange(roundedVal, highRef.current);
                }
            },
            onPanResponderRelease: () => {
                startLowRef.current = lowRef.current;
            },
        })
    ).current;

    const panHigh = useRef(
        PanResponder.create({
            onStartShouldSetPanResponder: () => true,
            onMoveShouldSetPanResponder: () => true,
            onPanResponderGrant: () => {
                startHighRef.current = highRef.current;
            },
            onPanResponderMove: (_, gesture) => {
                const width = sliderWidthRef.current;
                if (!width) return;
                const diff = (gesture.dx / width) * (max - min);
                let newVal = startHighRef.current + diff;
                newVal = Math.max(lowRef.current + 1, Math.min(newVal, max));
                const roundedVal = Math.round(newVal);
                if (roundedVal !== highRef.current) {
                    setHigh(roundedVal);
                    onValuesChange && onValuesChange(lowRef.current, roundedVal);
                }
            },
            onPanResponderRelease: () => {
                startHighRef.current = highRef.current;
            },
        })
    ).current;

    const lowPos = sliderWidth ? ((low - min) / (max - min)) * sliderWidth : 0;
    const highPos = sliderWidth ? ((high - min) / (max - min)) * sliderWidth : 0;

    return (
        <View style={styles.sliderContainer} onLayout={(e) => setSliderWidth(e.nativeEvent.layout.width)}>
            <View style={styles.trackBg}/>
            <View style={[styles.trackActive, {left: lowPos, width: Math.max(0, highPos - lowPos)}]}/>
            <View style={[styles.thumb, {left: lowPos - 14}]} {...panLow.panHandlers}/>
            <View style={[styles.thumb, {left: highPos - 14}]} {...panHigh.panHandlers}/>
            <View style={[styles.priceLabel, {left: lowPos - 27}]}>
                <CustomText style={styles.priceText}>${low}k</CustomText>
            </View>
            <View style={[styles.priceLabel, {left: highPos - 27}]}>
                <CustomText style={styles.priceText}>${high}k</CustomText>
            </View>
        </View>
    );
};

const CandidateSearchAdvance = ({navigation}) => {
    const [categories, setCategories] = useState([]);
    const [locations, setLocations] = useState([]);
    const [loadingData, setLoadingData] = useState(true);

    const [category, setCategory] = useState(null);
    const [subCategory, setSubCategory] = useState(null);
    const [location, setLocation] = useState(null);

    const DEFAULT_SALARY = {min: 0, max: 50};
    const [salary, setSalary] = useState(DEFAULT_SALARY);
    const [resetSliderTrigger, setResetSliderTrigger] = useState(0);

    const [selectedJobTypes, setSelectedJobTypes] = useState([]);
    const [lastUpdate, setLastUpdate] = useState('any');
    const [experience, setExperience] = useState(null);

    useEffect(() => {
        const fetchMasterData = async () => {
            try {
                const [resCats, resLocs] = await Promise.all([
                    API.get(endpoints['categories']),
                    API.get(endpoints['locations'])
                ]);

                setCategories(resCats.data);
                setLocations(resLocs.data);
            } catch (error) {
                console.error("Lỗi lấy dữ liệu lọc:", error);
            } finally {
                setLoadingData(false);
            }
        };

        fetchMasterData();
    }, []);

    const toggleJobType = (id) => {
        if (selectedJobTypes.includes(id)) {
            setSelectedJobTypes(prev => prev.filter(item => item !== id));
        } else {
            setSelectedJobTypes(prev => [...prev, id]);
        }
    };

    const handleReset = () => {
        console.log("Resetting filters...");
        setCategory(null);
        setSubCategory(null);
        setLocation(null);

        setSalary(DEFAULT_SALARY);
        setResetSliderTrigger(prev => prev + 1);

        setSelectedJobTypes([]);
        setLastUpdate('any');
        setExperience(null);
    };

    const handleApply = () => {
        const filterParams = {
            category,
            location,
            salary,
            selectedJobTypes,
            lastUpdate,
            experience
        };

        console.log("Applying filters:", filterParams);
        navigation.navigate('CandidateSearchResults', {filterParams});
    };

    return (
        <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
            <View style={{paddingHorizontal: 20}}>
                <View style={{
                    flexDirection: 'row',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingVertical: 10
                }}>
                    <TouchableOpacity onPress={() => navigation.goBack()}>
                        <MaterialCommunityIcons name="arrow-left" size={24} color="#130160"/>
                    </TouchableOpacity>
                    <CustomText style={styles.headerTitle}>Filter</CustomText>
                    <View style={{width: 24}}/>
                </View>
            </View>

            {loadingData ? (
                <View style={{flex: 1, justifyContent: 'center', alignItems: 'center'}}>
                    <ActivityIndicator size="large" color="#FF9228"/>
                    <CustomText>Loading filters...</CustomText>
                </View>
            ) : (
                <ScrollView contentContainerStyle={styles.scrollContainer} showsVerticalScrollIndicator={false}>
                    <View style={styles.sectionWrapper}>
                        <CustomSelector
                            label="Category"
                            placeholder="Select Category"
                            data={categories}
                            selectedValue={category}
                            onSelect={setCategory}
                        />
                        <View style={styles.separator}/>
                    </View>

                    <View style={styles.sectionWrapper}>
                        <CustomSelector
                            label="Location"
                            placeholder="Select Location"
                            data={locations}
                            selectedValue={location}
                            onSelect={setLocation}
                        />
                        <View style={styles.separator}/>
                    </View>

                    <View style={styles.sectionWrapper}>
                        <View style={styles.accordionHeader}>
                            <CustomText style={styles.sectionTitle}>Last update</CustomText>
                        </View>
                        <View style={styles.radioGroup}>
                            {UPDATE_TIMES.map((item) => {
                                const isSelected = lastUpdate === item.id;
                                return (
                                    <TouchableOpacity
                                        key={item.id}
                                        style={styles.radioRow}
                                        onPress={() => setLastUpdate(item.id)}
                                        activeOpacity={0.7}
                                    >
                                        <MaterialCommunityIcons
                                            name={isSelected ? "record-circle-outline" : "circle-outline"}
                                            size={24}
                                            color={isSelected ? "#FCA34D" : "#524B6B"}
                                        />
                                        <CustomText style={[styles.radioText, isSelected && styles.radioTextSelected]}>
                                            {item.label}
                                        </CustomText>
                                    </TouchableOpacity>
                                )
                            })}
                        </View>
                        <View style={styles.separator}/>
                    </View>

                    {/* Salary Slider */}
                    <View style={styles.sectionWrapper}>
                        <CustomText style={styles.sectionTitle}>Salary (Million VND)</CustomText>
                        <RangeSlider
                            min={0}
                            max={50}
                            initialLow={salary.min}
                            initialHigh={salary.max}
                            resetTrigger={resetSliderTrigger} // Truyền prop này để reset UI
                            onValuesChange={(min, max) => setSalary({min, max})}
                        />
                        <View style={{height: 5}}/>
                        <View style={styles.separator}/>
                    </View>

                    <View style={styles.sectionWrapper}>
                        <CustomText style={styles.sectionTitle}>Job Type</CustomText>
                        <View style={styles.chipContainer}>
                            {JOB_TYPES.map((type) => {
                                const isSelected = selectedJobTypes.includes(type.id);
                                return (
                                    <TouchableOpacity
                                        key={type.id}
                                        style={[styles.chipBtn, isSelected && styles.chipBtnSelected]}
                                        onPress={() => toggleJobType(type.id)}
                                    >
                                        <CustomText style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                                            {type.label}
                                        </CustomText>
                                    </TouchableOpacity>
                                )
                            })}
                        </View>
                    </View>

                    <View style={styles.sectionWrapper}>
                        <View style={styles.accordionHeader}>
                            <CustomText style={styles.sectionTitle}>Experience</CustomText>
                        </View>
                        <View style={styles.radioGroup}>
                            {EXPERIENCE_LEVELS.map((item) => {
                                const isSelected = experience === item.id;
                                return (
                                    <TouchableOpacity
                                        key={item.id}
                                        style={styles.radioRow}
                                        onPress={() => setExperience(item.id)}
                                        activeOpacity={0.7}
                                    >
                                        <MaterialCommunityIcons
                                            name={isSelected ? "record-circle-outline" : "circle-outline"}
                                            size={24}
                                            color={isSelected ? "#FCA34D" : "#524B6B"}
                                        />
                                        <CustomText style={[styles.radioText, isSelected && styles.radioTextSelected]}>
                                            {item.label}
                                        </CustomText>
                                    </TouchableOpacity>
                                )
                            })}
                        </View>
                    </View>
                </ScrollView>
            )}

            <CustomFooter applyTitle="APPLY NOW" onApply={handleApply}
                          leftContent={<ResetButton onPress={handleReset}/>}/>
        </SafeAreaView>
    );
};

export default CandidateSearchAdvance;