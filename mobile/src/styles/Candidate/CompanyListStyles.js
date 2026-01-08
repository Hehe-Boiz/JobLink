import { StyleSheet, Dimensions } from 'react-native';

const { width } = Dimensions.get('window');
const cardWidth = (width - 40 - 15) / 2;

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F9F9F9',
    },
    listContent: {
        paddingHorizontal: 20,
        paddingTop: 10,
        paddingBottom: 150,
    },
    columnWrapper: {
        justifyContent: 'space-between',
        marginBottom: 15,
    },

    cardContainer: {
        width: cardWidth,
        backgroundColor: '#FFFFFF',
        borderRadius: 20,
        paddingVertical: 25,
        paddingHorizontal: 15,
        alignItems: 'center',
        elevation: 3,
    },
    logoContainer: {
        width: 60,
        height: 60,
        borderRadius: 30,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 15,
        overflow: 'hidden',
    },
    logo: {
        width: 40,
        height: 40,
        resizeMode: 'contain'
    },
    companyName: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#0D0140',
        marginBottom: 5,
        textAlign: 'center',
    },
    followers: {
        fontSize: 14,
        color: '#AAA6B9',
        marginBottom: 15,
    },

    followBtn: {
        width: '100%',
        paddingVertical: 8,
        borderRadius: 20,
        borderWidth: 1,
        borderColor: '#7551FF',
        backgroundColor: '#FFFFFF',
        alignItems: 'center',
        justifyContent: 'center',
    },
    followBtnActive: {
        backgroundColor: '#130160',
        borderColor:'#130160'
    },
    btnText: {
        fontSize: 14,
        fontWeight: '500',
        color: '#0D0140',
    },
    btnTextActive: {
        color: '#FFFFFF',
    },

    searchContainer: {
        paddingHorizontal: 20,
        // marginTop: 3,
        marginBottom: 10,
        marginTop: 10,

    },
    searchBar: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFF',
        borderRadius: 15,
        paddingHorizontal: 15,
        height: 45,
        elevation: 2,
    },
    searchInput: {
        flex: 1,
        marginLeft: 10,
        fontSize: 14,
        color: '#130160',
    },
});

export default styles;