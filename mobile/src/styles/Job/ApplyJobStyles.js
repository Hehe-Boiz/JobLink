import {StyleSheet, Dimensions} from 'react-native';

const {width} = Dimensions.get('window');

export default StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: "#F9F9F9"
    },
    uploadBox: {
        borderWidth: 1.5,
        borderColor: '#9D97B5',
        borderStyle: 'dashed',
        borderRadius: 15,
        height: 90,
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'row',
        backgroundColor: '#FAFAFD',
    },
    uploadText: {
        marginLeft: 10,
        color: '#150B3D',
        fontSize: 14,
        fontWeight: '500',
    },
    filePreviewContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 5
    },
    fileIconBox: {
        marginRight: 15,
    },
    fileInfo: {
        flex: 1,
    },
    fileName: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#0D0140',
        marginBottom: 4,
    },
    fileSize: {
        fontSize: 12,
        color: '#95969D',
    },
    removeBtn: {
        padding: 5,
    },
    removeText: {
        fontSize: 12,
        color: '#FF4D4D',
        marginTop: 5,
        marginLeft: 4
    },
    inputArea: {
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        padding: 20,
        height: 200,
        textAlignVertical: 'top',
        fontSize: 13,
        color: '#0D0140',
        borderWidth: 1,
        borderColor: '#EAEAEA',
        elevation: 0.5,
        paddingTop: 20,
    },
    footer: {
        padding: 15,
        paddingBottom: 10,
    },
    applyBtn: {
        backgroundColor: '#130160',
        height: 56,
        borderRadius: 16,
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#130160',
        shadowOffset: {width: 0, height: 4},
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 5,
    },
    applyBtnText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
        textTransform: 'uppercase',
    },
    successContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingHorizontal: 30,
        backgroundColor: '#FFFFFF',
    },
    successImage: {
        width: 150,
        height: 150,
        marginBottom: 30,
    },
    successTitle: {
        fontSize: 22,
        fontWeight: 'bold',
        color: '#0D0140',
        marginBottom: 10,
    },
    successDesc: {
        fontSize: 14,
        color: '#524B6B',
        textAlign: 'center',
        marginBottom: 40,
        lineHeight: 22,
    },
    secondaryBtn: {
        backgroundColor: '#E6E1FF', // Tím nhạt
        width: '100%',
        height: 56,
        borderRadius: 16,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 15,
    },
    secondaryBtnText: {
        color: '#130160',
        fontWeight: 'bold',
        fontSize: 16,
    },
    primaryBtn: {
        backgroundColor: '#130160',
        width: '100%',
        height: 56,
        borderRadius: 16,
        justifyContent: 'center',
        alignItems: 'center',
    },
    fileSuccessContainer: {
        borderRadius: 20,
        borderStyle: 'dashed',
        borderWidth: 0.8,
        padding: 20,
        borderColor: "#9D97B5",
        backgroundColor: 'rgba(63, 19, 228, 0.05)',
    }
});