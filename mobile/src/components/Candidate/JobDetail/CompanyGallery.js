import React, { useState } from 'react';
import { View, Image, TouchableOpacity, Modal, StatusBar, FlatList, Dimensions } from 'react-native';
import CustomText from '../../CustomText';
import styles from '../../../styles/Candidate/CandidateJobDetailStyles';
import { MaterialCommunityIcons } from '@expo/vector-icons';

const { width } = Dimensions.get('window');

const CompanyGallery = ({ images }) => {
    const [modalVisible, setModalVisible] = useState(false);
    const [currentIndex, setCurrentIndex] = useState(1);

    if (!images || images.length === 0) return null;
    const remainingCount = images.length > 2 ? images.length - 2 : 0;

    const handleScroll = (event) => {
        const contentOffsetX = event.nativeEvent.contentOffset.x;
        const index = Math.round(contentOffsetX / width) + 1;
        setCurrentIndex(index);
    };

    const renderGalleryItem = ({ item }) => (
        <View style={styles.modalImageWrapper}>
            <Image
                source={{ uri: item }}
                style={styles.modalImage}
                resizeMode="contain"
            />
        </View>
    );

    return (
        <View style={styles.gallerySection}>
            <CustomText style={styles.contentTitle}>Company Gallery</CustomText>

            <View style={styles.galleryContainer}>
                {/* Ảnh chính 1 */}
                <TouchableOpacity
                    style={styles.galleryItem}
                    onPress={() => setModalVisible(true)}
                >
                    <Image source={{ uri: images[0] }} style={styles.galleryImage} resizeMode="cover" />
                </TouchableOpacity>

                {/* Ảnh 2 & Nút xem thêm */}
                {images.length > 1 && (
                    <TouchableOpacity
                        style={styles.galleryItem}
                        onPress={() => setModalVisible(true)}
                    >
                        <Image source={{ uri: images[1] }} style={styles.galleryImage} resizeMode="cover" />
                        {remainingCount > 0 && (
                            <View style={styles.galleryOverlay}>
                                <CustomText style={styles.galleryMoreText}>
                                    +{remainingCount} pictures
                                </CustomText>
                            </View>
                        )}
                    </TouchableOpacity>
                )}
            </View>

            <Modal
                animationType="slide"
                transparent={true}
                visible={modalVisible}
                onRequestClose={() => setModalVisible(false)}
            >
                <View style={styles.modalContainer}>
                    <StatusBar barStyle="light-content" />

                    <View style={styles.modalHeader}>
                        <CustomText style={styles.paginationText}>
                            {currentIndex} / {images.length}
                        </CustomText>

                        <TouchableOpacity
                            style={styles.modalCloseButton}
                            onPress={() => setModalVisible(false)}
                        >
                            <MaterialCommunityIcons name="close" size={24} color="#FFFFFF" />
                        </TouchableOpacity>
                    </View>

                    <FlatList
                        data={images}
                        renderItem={renderGalleryItem}
                        keyExtractor={(item, index) => index.toString()}
                        horizontal
                        pagingEnabled
                        showsHorizontalScrollIndicator={false}
                        onScroll={handleScroll}
                        scrollEventThrottle={16}
                    />

                    <View style={styles.modalFooter}>
                        <CustomText style={styles.footerHint}>VUỐT ĐỂ XEM THÊM</CustomText>
                    </View>
                </View>
            </Modal>
        </View>
    );
};

export default CompanyGallery;